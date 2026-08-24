"""Dependency and Ansible collection support policy tests."""

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
    ansible_name = canonicalize_name("ansible")
    ansible = [
        requirement for requirement in _project_dependencies() if canonicalize_name(requirement.name) == ansible_name
    ]

    assert len(ansible) == 1, "project dependencies must contain exactly one ansible requirement"
    requirement = ansible[0]
    assert requirement.marker is None, "the ansible requirement must apply unconditionally"
    specifiers = list(requirement.specifier)
    assert len(specifiers) == 1, "ansible must have one exact version"
    assert specifiers[0].operator == "==", "ansible must use an exact == pin"
    assert "*" not in specifiers[0].version, "ansible must not use a wildcard version"
    assert Version(specifiers[0].version).major >= 14, "ansible must use maintained major version 14 or newer"


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
