"""Validate file component rules before deployment or enrollment writes."""

import os
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]


def run_tasks(tmp_path, tasks, variables):
    play = {"hosts": "localhost", "gather_facts": False, "tasks": tasks, "vars": variables}
    playbook = tmp_path / "test.yml"
    playbook.write_text(yaml.safe_dump([play]))
    return subprocess.run(
        [sys.executable, "-m", "ansible.cli.playbook", "-i", "localhost,", "-c", "local", str(playbook)],
        env={**os.environ, "ANSIBLE_LOCAL_TEMP": str(tmp_path / "controller")},
        capture_output=True,
        text=True,
        check=False,
        timeout=40,
    )


@pytest.mark.parametrize(
    ("users", "endpoint", "accepted"),
    [
        (["phone-1", "0002", "A_B.c"], "vpn.example.test", True),
        (["phone"], "2001:db8::1", True),
        (["Alice", "alice"], "vpn", False),
        (["phone/one"], "vpn", False),
        (["CON.txt"], "vpn", False),
        (["phone"], "group/name", False),
        (["phone"], "nul.old", False),
        (["vpn"], "VPN", False),
        ([123], "vpn", False),
        ("phone", "vpn", False),
    ],
)
def test_config_names(tmp_path, users, endpoint, accepted):
    result = run_tasks(
        tmp_path,
        [{"import_tasks": str(ROOT / "playbooks/validate-config-names.yml")}],
        {"config_users": users, "config_endpoint": endpoint},
    )
    assert (result.returncode == 0) == accepted, result.stdout + result.stderr
