"""Dependency and Ansible collection support policy tests."""

import configparser
import re
import tomllib
from pathlib import Path

import yaml
from packaging.requirements import Requirement
from packaging.specifiers import SpecifierSet
from packaging.utils import canonicalize_name
from packaging.version import InvalidVersion, Version

ROOT = Path(__file__).parents[2]


def _project_configuration():
    configuration = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert isinstance(configuration, dict), "pyproject.toml must contain a top-level mapping"
    return configuration


def _collections():
    document = yaml.safe_load((ROOT / "requirements.yml").read_text(encoding="utf-8"))
    assert isinstance(document, dict), "requirements.yml must contain a top-level mapping"
    collections = document.get("collections")
    assert isinstance(collections, list) and collections, "requirements.yml must contain a nonempty collections list"
    return collections


def _project_dependencies():
    project = _project_configuration().get("project")
    assert isinstance(project, dict), "pyproject.toml must contain a [project] mapping"
    dependencies = project.get("dependencies")
    assert isinstance(dependencies, list) and dependencies, "project.dependencies must be a nonempty list"
    assert all(isinstance(dependency, str) for dependency in dependencies), "every project dependency must be a string"
    return [Requirement(dependency) for dependency in dependencies]


def _requirements(values, source):
    assert isinstance(values, list) and values, f"{source} must be a nonempty list"
    assert all(isinstance(value, str) for value in values), f"every {source} entry must be a string"
    return [Requirement(value) for value in values]


def _requirement_named(requirements, name):
    normalized_name = canonicalize_name(name)
    matches = [requirement for requirement in requirements if canonicalize_name(requirement.name) == normalized_name]
    assert len(matches) == 1, f"must contain exactly one {name} requirement"
    assert matches[0].marker is None, f"the {name} requirement must apply unconditionally"
    return matches[0]


def _exact_collection_version(collection):
    assert isinstance(collection, dict), "each collection entry must be a mapping"
    name = collection.get("name", "<unnamed>")
    version = collection.get("version")
    assert isinstance(version, str), f"{name} must declare a string version"
    specifiers = list(SpecifierSet(version))
    assert len(specifiers) == 1, f"{collection['name']} must have one exact version"
    specifier = specifiers[0]
    assert specifier.operator == "==", f"{collection['name']} must use ==, not {specifier.operator}"
    assert "*" not in specifier.version, f"{collection['name']} must not use a wildcard version"
    try:
        return Version(specifier.version)
    except InvalidVersion as error:
        raise AssertionError(f"{collection['name']} has an invalid version: {specifier.version}") from error


def test_ansible_is_exactly_pinned_to_a_maintained_major():
    requirement = _requirement_named(_project_dependencies(), "ansible")
    specifiers = list(requirement.specifier)
    assert len(specifiers) == 1, "ansible must have one exact version"
    assert specifiers[0].operator == "==", "ansible must use an exact == pin"
    assert "*" not in specifiers[0].version, "ansible must not use a wildcard version"
    assert Version(specifiers[0].version).major >= 14, "ansible must use maintained major version 14 or newer"


def test_controller_dependencies_have_patched_security_floors():
    configuration = _project_configuration()
    build_requirements = _requirements(configuration["build-system"]["requires"], "build-system.requires")
    project_requirements = _project_dependencies()
    optional_dependencies = configuration["project"]["optional-dependencies"]
    gcp_requirements = _requirements(optional_dependencies["gcp"], "project.optional-dependencies.gcp")

    setuptools = _requirement_named(build_requirements, "setuptools").specifier
    assert Version("82.999") not in setuptools
    assert Version("83.0.0") in setuptools
    cryptography = _requirement_named(project_requirements, "cryptography").specifier
    assert Version("49.999") not in cryptography
    assert Version("50.0.0") in cryptography
    assert Version("51.0.0") not in cryptography
    pyasn1 = _requirement_named(gcp_requirements, "pyasn1").specifier
    assert Version("0.6.3") not in pyasn1
    assert Version("0.6.4") in pyasn1


def test_controller_requires_python_3_12_or_newer():
    requires_python = SpecifierSet(_project_configuration()["project"]["requires-python"])

    assert Version("3.11") not in requires_python
    assert Version("3.12") in requires_python


def test_lock_contains_patched_click():
    configuration = _project_configuration()
    dev_requirements = _requirements(configuration["dependency-groups"]["dev"], "dependency-groups.dev")
    click_requirement = _requirement_named(dev_requirements, "click").specifier
    lock = tomllib.loads((ROOT / "uv.lock").read_text(encoding="utf-8"))
    click = [package for package in lock["package"] if canonicalize_name(package["name"]) == "click"]

    assert Version("8.3.2") not in click_requirement
    assert Version("8.3.3") in click_requirement
    assert len(click) == 1
    assert Version(click[0]["version"]) >= Version("8.3.3")


def test_uv_uses_dependency_groups_and_a_resolution_cooldown():
    configuration = _project_configuration()
    tool = configuration.get("tool")
    dependency_groups = configuration.get("dependency-groups")

    assert isinstance(tool, dict), "pyproject.toml must contain a [tool] mapping"
    uv = tool.get("uv")
    assert isinstance(uv, dict), "pyproject.toml must contain a [tool.uv] mapping"
    assert isinstance(dependency_groups, dict), "pyproject.toml must contain a [dependency-groups] mapping"
    dev = dependency_groups.get("dev")
    assert isinstance(dev, list) and dev, "[dependency-groups].dev must be a nonempty list"
    assert all(isinstance(dependency, str) for dependency in dev), "every dev dependency must be a string"

    assert "dev-dependencies" not in uv, "deprecated [tool.uv].dev-dependencies must not be used"
    assert uv.get("exclude-newer") == "7 days", "[tool.uv].exclude-newer must be 7 days"


def test_all_collections_are_uniquely_and_exactly_pinned():
    collections = _collections()
    names = [collection["name"].casefold() for collection in collections]

    assert len(names) == len(set(names)), "collection names must be unique"
    for collection in collections:
        _exact_collection_version(collection)


def test_ansible_posix_contains_authorized_key_fix():
    matches = [collection for collection in _collections() if collection.get("name", "").casefold() == "ansible.posix"]

    assert len(matches) == 1, "requirements.yml must contain exactly one ansible.posix collection"
    assert _exact_collection_version(matches[0]) >= Version("2.2.1"), "ansible.posix must be 2.2.1 or newer"


def test_ansible_uses_only_the_project_collection_path():
    configuration = configparser.ConfigParser()
    configuration.read(ROOT / "ansible.cfg", encoding="utf-8")

    value = configuration["defaults"]["collections_path"]
    paths = [path.strip() for path in value.split(":") if path.strip()]
    assert paths == ["./.ansible/collections"]


def test_collection_installers_are_project_local_and_fail_closed():
    expected = "uv run ansible-galaxy collection install --force -p .ansible/collections -r requirements.yml"
    launcher = (ROOT / "algo").read_text(encoding="utf-8")
    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")

    launcher_commands = [line.strip() for line in launcher.splitlines() if "ansible-galaxy collection install" in line]
    docker_commands = [
        line.removeprefix("RUN ").strip()
        for line in dockerfile.splitlines()
        if "ansible-galaxy collection install" in line
    ]
    assert launcher_commands == [expected]
    assert docker_commands == [expected]
    assert not re.search(r"ansible-galaxy collection install[^\n]*(?:\|\|\s*true|2>\s*/dev/null)", launcher)


def test_project_collection_directory_is_ignored_explicitly():
    ignored = {line.strip() for line in (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()}
    docker_ignored = {line.strip() for line in (ROOT / ".dockerignore").read_text(encoding="utf-8").splitlines()}

    assert ".ansible/collections/" in ignored
    assert ".ansible/" in docker_ignored
