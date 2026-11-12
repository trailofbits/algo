"""Exercise production Ansible tasks without changing the host configuration."""

import base64
import configparser
import json
import os
import subprocess
import sys
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey


def test_ansible_smoke(tmp_path: Path) -> None:
    """Run local setup, create real keys, and validate a rendered client config."""
    root = Path(__file__).resolve().parents[1]
    variables = {
        "algo_root": str(root),
        "smoke_dir": str(tmp_path),
        "ansible_python_interpreter": sys.executable,
        "provider": "local",
        "server": "localhost",
        "server_name": "smoke_test",
        "endpoint": "192.0.2.1",
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
            str(root / "tests" / "ansible-smoke.yml"),
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
    assert config["Peer"]["Endpoint"] == "192.0.2.1:51820"
    assert config["Peer"]["AllowedIPs"] == "0.0.0.0/0,::/0"
    assert config["Interface"]["Address"] == "10.49.0.2"
    assert config["Interface"]["DNS"] == "1.1.1.1,1.0.0.1"

    for section, field in (
        ("Interface", "PrivateKey"),
        ("Peer", "PublicKey"),
        ("Peer", "PresharedKey"),
    ):
        assert len(base64.b64decode(config[section][field], validate=True)) == 32
    server_key = (tmp_path / "pki" / "private" / "192.0.2.1.raw").read_bytes()
    private_key = X25519PrivateKey.from_private_bytes(server_key)
    expected_public = private_key.public_key().public_bytes_raw()
    assert base64.b64decode(config["Peer"]["PublicKey"], validate=True) == expected_public
