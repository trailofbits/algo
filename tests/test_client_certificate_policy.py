"""Exercise migration of the historical Linux client setting."""

import os
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
ROLE = ROOT / "roles/client"


@pytest.mark.parametrize("state", ["absent", "algo", "custom"])
def test_remove_only_algo_override(tmp_path, state):
    target = tmp_path / "strongswan.d/relax-ca-constraints.conf"
    target.parent.mkdir()
    if state == "algo":
        target.write_bytes((ROLE / "files/libstrongswan-relax-constraints.conf").read_bytes())
    elif state == "custom":
        target.write_text("# managed by the system administrator")
    tasks = yaml.safe_load((ROLE / "tasks/main.yml").read_text())
    start = next(i for i, task in enumerate(tasks) if task.get("register") == "client_certificate_override")
    play = {
        "hosts": "localhost",
        "gather_facts": False,
        "tasks": tasks[start : start + 2],
        "vars": {"configs_prefix": str(tmp_path), "role_path": str(ROLE), "ansible_python_interpreter": sys.executable},
        "handlers": [{"name": "restart strongswan", "debug": {"msg": "reload recorded"}}],
    }
    playbook = tmp_path / "check.yml"
    playbook.write_text(yaml.safe_dump([play]))
    result = subprocess.run(
        [sys.executable, "-m", "ansible.cli.playbook", "-i", "localhost,", "-c", "local", str(playbook)],
        env={**os.environ, "ANSIBLE_LOCAL_TEMP": str(tmp_path / "temp")},
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert target.exists() == (state == "custom")
    assert ("reload recorded" in result.stdout) == (state == "algo")
