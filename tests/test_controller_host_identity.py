"""Inspect OpenSSH settings and preserve prior host keys across management runs."""

import os
import shlex
import subprocess
import sys
from pathlib import Path

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


def test_deployment_known_hosts(tmp_path):
    folder = tmp_path / "configs/server"
    folder.mkdir(parents=True)
    known = folder / "known_hosts"
    known.write_text("# existing host record\n")
    tasks = [
        {"import_tasks": str(ROOT / "playbooks/ssh-trust.yml")},
        {"copy": {"content": "{{ algo_ssh_trust_args }}", "dest": str(tmp_path / "args"), "mode": "0600"}},
    ]
    result = run_tasks(tmp_path, tasks, {"IP_subject_alt_name": "server", "ansible_python_interpreter": sys.executable})
    assert result.returncode == 0, result.stdout + result.stderr
    assert known.read_text() == "# existing host record\n"
    assert known.stat().st_mode & 0o777 == 0o600
    args = shlex.split((tmp_path / "args").read_text())
    config = subprocess.check_output(["ssh", "-G", *args, "test.invalid"], text=True).lower()
    assert "stricthostkeychecking accept-new" in config
    assert str(known).lower() in config
