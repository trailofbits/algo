"""Check that only explicit one-time provisioning discards WireGuard state."""

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


@pytest.mark.parametrize(("keep", "tmpfs"), [(True, False), (True, True), (False, False), (False, True)])
def test_retention(tmp_path, keep, tmpfs):
    state = tmp_path / "saved"
    state.mkdir()
    key = state / "index.txt"
    key.write_text("alice\n")
    tasks = yaml.safe_load((ROOT / "roles/wireguard/tasks/main.yml").read_text())
    cleanup = next(task for task in tasks if task.get("name", "").startswith("Discard WireGuard"))
    result = run_tasks(
        tmp_path,
        [cleanup],
        {
            "wireguard_store_keys": keep,
            "pki_in_tmpfs": tmpfs,
            "algo_store_pki": False,
            "wireguard_pki_path": str(state),
            "ansible_python_interpreter": sys.executable,
        },
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert key.exists() == keep
