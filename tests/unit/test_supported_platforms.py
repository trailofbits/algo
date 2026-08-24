from pathlib import Path

import pytest
import yaml
from jinja2.nativetypes import NativeEnvironment

ROOT = Path(__file__).parents[2]
COMMON_TASKS = ROOT / "roles/common/tasks/main.yml"
SUPPORTED_ERROR = "Algo supports only Ubuntu 22.04 LTS and Ubuntu 24.04 LTS."


def _platform_assertion():
    tasks = yaml.safe_load(COMMON_TASKS.read_text())
    return next(task for task in tasks if "assert" in task)


def _is_supported(distribution: str, version: str) -> bool:
    expression = _platform_assertion()["assert"]["that"]
    return bool(
        NativeEnvironment().compile_expression(expression)(
            ansible_distribution=distribution,
            ansible_distribution_version=version,
        )
    )


@pytest.mark.parametrize("version", ["22.04", "24.04"])
def test_supported_ubuntu_lts_releases_are_accepted(version):
    assert _is_supported("Ubuntu", version)


@pytest.mark.parametrize(
    ("distribution", "version"),
    [("Debian", "12"), ("Fedora", "40"), ("Ubuntu", "26.04")],
)
def test_other_distributions_and_ubuntu_releases_are_rejected(distribution, version):
    assert not _is_supported(distribution, version)


def test_platform_error_lists_exact_supported_releases():
    assertion = _platform_assertion()["assert"]
    assert assertion["fail_msg"] == SUPPORTED_ERROR


def test_platform_is_validated_before_ubuntu_tasks():
    tasks = yaml.safe_load(COMMON_TASKS.read_text())
    assertion_index = next(i for i, task in enumerate(tasks) if "assert" in task)
    ubuntu_index = next(i for i, task in enumerate(tasks) if task.get("include_tasks") == "ubuntu.yml")
    assert assertion_index < ubuntu_index


def test_local_prompt_and_documentation_name_both_supported_releases():
    prompt = (ROOT / "input.yml").read_text()
    documentation = (ROOT / "docs/deploy-to-ubuntu.md").read_text()
    assert "Ubuntu 22.04 or 24.04 LTS" in prompt
    assert "Ubuntu 22.04 LTS and Ubuntu 24.04 LTS" in documentation
    assert "latest LTS" not in prompt
