"""Run user-update preflight checks without changing accounts or VPN services."""

import json
import os
import pwd
import socket
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("scenario", ["local", "wrong-owner", "unreachable"])
def test_user_preflight(tmp_path: Path, scenario: str):
    # Exercise the same production task file imported by users.yml.
    playbook = tmp_path / "preflight.yml"
    preflight = str(ROOT / "playbooks/user-preflight.yml")
    playbook.write_text(
        yaml.safe_dump(
            [
                {
                    "name": "Check user-update prerequisites",
                    "hosts": "localhost",
                    "gather_facts": False,
                    "tasks": [{"ansible.builtin.import_tasks": preflight}],
                }
            ]
        )
    )
    (tmp_path / "configs/localhost").mkdir(parents=True)
    variables = {
        "algo_server": "localhost",
        "algo_provider": "local",
        "ansible_connection": "local",
        "ansible_python_interpreter": sys.executable,
    }
    if scenario == "wrong-owner":
        variables["ansible_user_id"] = "different-user"
    # Hold a local port open without listening so no other process can claim it.
    with socket.socket() as port:
        port.bind(("127.0.0.1", 0))
        if scenario == "unreachable":
            variables.update(
                algo_server="127.0.0.1",
                algo_provider="ec2",
                ansible_ssh_port=port.getsockname()[1],
            )
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "ansible.cli.playbook",
                str(playbook),
                "-i",
                "localhost,",
                "-c",
                "local",
                "-e",
                json.dumps(variables),
            ],
            cwd=tmp_path,
            env={
                **os.environ,
                "ANSIBLE_LOCAL_TEMP": str(tmp_path / "controller-tmp"),
                "ANSIBLE_REMOTE_TEMP": str(tmp_path / "module-tmp"),
            },
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
    output = result.stdout + result.stderr
    if scenario == "local":
        assert result.returncode == 0, output
    elif scenario == "wrong-owner":
        assert result.returncode != 0
        assert "PERMISSION MISMATCH" in output
        assert pwd.getpwuid(os.getuid()).pw_name in output
    else:
        assert result.returncode != 0
        assert "Cannot connect to 127.0.0.1" in output
