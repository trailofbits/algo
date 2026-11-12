"""Reject path traversal before destroy reads configuration or removes files."""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize(
    ("server", "valid"),
    [
        ("../victim", False),
        ("..", False),
        (".", False),
        ("", False),
        ("192.0.2.1", True),
        ("2001:db8::1", True),
        ("vpn.example.com", True),
    ],
)
def test_destroy_only_removes_one_server_directory(tmp_path: Path, server: str, valid: bool):
    shutil.copy(ROOT / "destroy.yml", tmp_path)
    shutil.copy(ROOT / "config.cfg", tmp_path)
    (tmp_path / "playbooks").mkdir()
    shutil.copy(ROOT / "playbooks/rescue.yml", tmp_path / "playbooks")
    (tmp_path / "configs").mkdir()
    victim = tmp_path / "victim"
    victim.mkdir()
    (victim / ".config.yml").write_text("algo_provider: local\nalgo_server_name: victim\n")
    if valid:
        target = tmp_path / "configs" / server
        target.mkdir()
        shutil.copy(victim / ".config.yml", target)
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "ansible.cli.playbook",
            str(tmp_path / "destroy.yml"),
            "-i",
            "localhost,",
            "-c",
            "local",
            "-e",
            json.dumps(
                {
                    "server_ip": server,
                    "confirm_destroy": True,
                    "ansible_connection": "local",
                    "ansible_python_interpreter": sys.executable,
                }
            ),
        ],
        cwd=tmp_path,
        env={
            **os.environ,
            "ANSIBLE_LOCAL_TEMP": str(tmp_path / "ansible-tmp"),
            "ANSIBLE_REMOTE_TEMP": str(tmp_path / "module-tmp"),
        },
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    if valid:
        assert result.returncode == 0, result.stdout + result.stderr
        assert not (tmp_path / "configs" / server).exists()
    else:
        assert result.returncode != 0, result.stdout + result.stderr
        assert "single server directory" in result.stdout
    assert (victim / ".config.yml").exists()
