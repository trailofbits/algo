"""Check endpoint admission against the actual IPsec signing policy."""

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
    ("endpoint", "ipsec", "accepted"),
    [
        ("vpn.example.com", True, False),
        ("10.12.0.1", True, False),
        ("fd12::2", True, False),
        ("vpn.example.test", True, True),
        ("203.0.113.3", True, True),
        ("2001:4860::1", True, True),
        ("vpn.example.com", False, True),
    ],
)
def test_endpoint_policy(tmp_path, endpoint, ipsec, accepted):
    tasks = [{"import_tasks": str(ROOT / "playbooks/ipsec-endpoint.yml")}]
    result = run_tasks(tmp_path, tasks, {"IP_subject_alt_name": endpoint, "ipsec_enabled": ipsec})
    assert (result.returncode == 0) == accepted, result.stdout + result.stderr
    if not accepted:
        assert "The IPsec CA excludes" in result.stdout
