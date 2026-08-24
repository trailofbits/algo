"""Ubuntu 26.04 stays gated until the complete provider-canary matrix exists."""

from pathlib import Path

import yaml


def test_server_preflight_rejects_unvalidated_ubuntu_releases():
    tasks = yaml.safe_load(Path("roles/common/tasks/ubuntu.yml").read_text(encoding="utf-8"))
    gate = next(task for task in tasks if task.get("name") == "Validate the Ubuntu server release")
    assertion = gate["assert"]

    assert "ansible_distribution == 'Ubuntu'" in assertion["that"]
    assert "ansible_distribution_version in ['22.04', '24.04']" in assertion["that"]
    assert "26.04" in assertion["fail_msg"]
    assert "not supported" in assertion["fail_msg"]


def test_ubuntu_2604_is_not_advertised_without_provider_canaries():
    advertised_sources = [
        Path("config.cfg"),
        Path("README.md"),
        Path("docs/deploy-to-ubuntu.md"),
        Path("docs/deploy-to-unsupported-cloud.md"),
    ]
    for source in advertised_sources:
        assert "26.04" not in source.read_text(encoding="utf-8"), source
