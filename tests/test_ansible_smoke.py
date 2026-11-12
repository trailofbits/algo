"""Exercise production Ansible tasks without changing the host configuration."""

import base64
import configparser
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey


@pytest.mark.parametrize(
    ("endpoint", "keepalive"),
    [("192.0.2.1", 0), ("192.0.2.1", 25), ("2001:db8::1", 25), ("vpn.example.com", 25)],
)
def test_ansible_smoke(tmp_path: Path, endpoint: str, keepalive: int) -> None:
    """Run local setup, create real keys, and validate a rendered client config."""
    root = Path(__file__).resolve().parents[1]
    playbook = tmp_path / "smoke.yml"
    shutil.copy(root / "tests" / "ansible-smoke.yml", playbook)
    (tmp_path / "files").symlink_to(root / "files", target_is_directory=True)
    private_dir = tmp_path / "pki" / "private"
    private_dir.mkdir(parents=True)
    (private_dir / "smoke-user.raw").write_bytes(b"\t" + b"\x01" * 30 + b"\n")
    variables = {
        "algo_root": str(root),
        "smoke_dir": str(tmp_path),
        "ansible_python_interpreter": sys.executable,
        "provider": "local",
        "server": "localhost",
        "server_name": "smoke_test",
        "endpoint": endpoint,
        "users": ["smoke-user"],
        "ondemand_cellular": False,
        "ondemand_wifi": False,
        "dns_adblocking": False,
        "ssh_tunneling": False,
        "local_install_confirmed": True,
        "ipsec_enabled": False,
        "pki_in_tmpfs": False,
        "dns_encryption": False,
        "ipv6_support": False,
        "wireguard_pki_path": str(tmp_path / "pki"),
        "wireguard_PersistentKeepalive": keepalive,
    }
    environment = {
        **os.environ,
        "ANSIBLE_CONFIG": str(root / "ansible.cfg"),
        "ANSIBLE_LIBRARY": str(root / "library"),
        "ANSIBLE_LOCAL_TEMP": str(tmp_path / "controller-tmp"),
        "ANSIBLE_REMOTE_TEMP": str(tmp_path / "module-tmp"),
        "ANSIBLE_NOCOLOR": "1",
        "ANSIBLE_FORCE_COLOR": "0",
    }
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "ansible.cli.playbook",
            str(playbook),
            "--inventory",
            "localhost,",
            "--connection",
            "local",
            "--extra-vars",
            json.dumps(variables),
        ],
        cwd=root,
        env=environment,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    assert result.returncode == 0, f"Ansible smoke test failed:\n{result.stdout}\n{result.stderr}"

    config = configparser.ConfigParser(interpolation=None)
    config.read_string((tmp_path / "client.conf").read_text())
    assert config.sections() == ["Interface", "Peer"]
    host = f"[{endpoint}]" if ":" in endpoint else endpoint
    assert config["Peer"]["Endpoint"] == f"{host}:51820"
    if keepalive:
        assert config["Peer"].getint("PersistentKeepalive") == keepalive
    else:
        assert "PersistentKeepalive" not in config["Peer"]
    assert config["Peer"]["AllowedIPs"] == "0.0.0.0/0,::/0"
    assert config["Interface"]["Address"] == "10.49.0.2"
    assert config["Interface"]["DNS"] == "1.1.1.1,1.0.0.1"

    for section, field in (
        ("Interface", "PrivateKey"),
        ("Peer", "PublicKey"),
        ("Peer", "PresharedKey"),
    ):
        assert len(base64.b64decode(config[section][field], validate=True)) == 32
    server_key = (tmp_path / "pki" / "private" / f"{endpoint}.raw").read_bytes()
    private_key = X25519PrivateKey.from_private_bytes(server_key)
    expected_public = private_key.public_key().public_bytes_raw()
    assert base64.b64decode(config["Peer"]["PublicKey"], validate=True) == expected_public
