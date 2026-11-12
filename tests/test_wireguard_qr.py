"""Exercise production QR tasks with the controller's installed Segno library."""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("writable", [True, False])
def test_qr_generation_without_cli_on_path(tmp_path: Path, writable: bool):
    configs = tmp_path / "config with spaces"
    configs.mkdir()
    content = "[Interface]\nPrivateKey = example-secret\n[Peer]\nEndpoint = vpn.example:51820\n"
    (configs / "test-user.conf").write_text(content)
    output = configs / "test-user.png"
    if writable:
        output.write_bytes(b"old QR image")
        output.chmod(0o644)
    else:
        output.mkdir()
    task = ROOT / "roles/wireguard/tasks/qr.yml"
    play = [
        {
            "name": "Generate QR",
            "hosts": "localhost",
            "gather_facts": False,
            "tasks": [{"ansible.builtin.import_tasks": str(task)}],
        }
    ]
    playbook = tmp_path / "qr.yml"
    playbook.write_text(yaml.safe_dump(play))
    variables = {
        "wireguard_config_path": str(configs),
        "wireguard_users": ["test-user", "removed-user"],
        "users": ["test-user"],
        "ansible_python_interpreter": sys.executable,
    }
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
        env={
            **os.environ,
            "PATH": "/usr/bin:/bin",
            "ANSIBLE_LOCAL_TEMP": str(tmp_path / "local"),
            "ANSIBLE_REMOTE_TEMP": str(tmp_path / "remote"),
        },
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert "example-secret" not in result.stdout + result.stderr
    if not writable:
        assert result.returncode != 0
        return
    assert result.returncode == 0, result.stdout + result.stderr
    assert output.read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
    assert output.stat().st_mode & 0o777 == 0o600
    assert not (configs / "removed-user.png").exists()
    decoder = shutil.which("zbarimg")
    if os.environ.get("ALGO_NETWORK_RUNTIME") == "1":
        assert decoder, "Install zbarimg in the network test container"
    if decoder:
        decoded = subprocess.run(
            [decoder, "--quiet", "--raw", str(output)],
            capture_output=True,
            text=True,
            check=True,
        )
        assert decoded.stdout == content + "\n"
