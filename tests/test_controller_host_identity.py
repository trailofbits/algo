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
    tmp_path = tmp_path / "workspace with spaces"
    folder = tmp_path / "configs/server"
    folder.mkdir(parents=True)
    known = folder / "known_hosts"
    known.write_text("# existing host record\n")
    server = yaml.safe_load((ROOT / "server.yml").read_text())[0]["tasks"][0]["block"]
    config_task = next(
        task for block in server for task in block.get("block", []) if task.get("name") == "Dump the ssh config"
    )
    config_task["copy"]["dest"] = str(folder / "ssh_config")
    tasks = [
        {"import_tasks": str(ROOT / "playbooks/ssh-trust.yml")},
        config_task,
        {"copy": {"content": "{{ algo_ssh_trust_args }}", "dest": str(tmp_path / "args"), "mode": "0600"}},
    ]
    key = tmp_path / "management key"
    result = run_tasks(
        tmp_path,
        tasks,
        {
            "IP_subject_alt_name": "server",
            "ansible_python_interpreter": sys.executable,
            "algo_server_name": "test-vpn",
            "ansible_ssh_user": "algo",
            "ansible_ssh_port": 2222,
            "SSH_keys": {"private": str(key)},
        },
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert known.read_text() == "# existing host record\n"
    assert known.stat().st_mode & 0o777 == 0o600
    args = shlex.split((tmp_path / "args").read_text())
    assert f'UserKnownHostsFile="{known}"' in args
    for address in ("test.invalid", "198.51.100.30"):
        config = subprocess.check_output(["ssh", "-G", *args, address], text=True).lower()
        assert "stricthostkeychecking accept-new" in config
        assert "hostkeyalias server" in config
        assert str(known).lower() in config
    saved = subprocess.check_output(["ssh", "-G", "-F", str(folder / "ssh_config"), "test-vpn"], text=True).lower()
    assert "hostkeyalias server" in saved and "hostname localhost" in saved
    assert f"identityfile {str(key).lower()}" in saved
    assert f"userknownhostsfile {str(known).lower()}" in saved
