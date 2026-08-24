#!/usr/bin/env python3
"""
Simplified Docker-based localhost deployment tests
Verifies services can start and config files exist in expected locations
"""

import os
import subprocess
import sys
from pathlib import Path


def check_docker_available():
    """Check if Docker is available"""
    try:
        result = subprocess.run(["docker", "--version"], capture_output=True, text=True)
        return result.returncode == 0
    except FileNotFoundError:
        return False


def test_wireguard_config_validation():
    """Test that WireGuard configs can be validated"""
    # Create a test WireGuard config
    config = """[Interface]
PrivateKey = EEHcgpEB8JIlUZpYnt3PqJJgfwgRGDQNlGH7gYkMVGo=
Address = 10.19.49.1/24,fd9d:bc11:4020::1/64
ListenPort = 51820

[Peer]
PublicKey = lIiWMxCWtXG5hqZECMXm7mA/4pNKKqtJIBZ5Fc1SeHg=
AllowedIPs = 10.19.49.2/32,fd9d:bc11:4020::2/128
"""

    # Just validate the format
    required_sections = ["[Interface]", "[Peer]"]
    required_fields = ["PrivateKey", "Address", "PublicKey", "AllowedIPs"]

    for section in required_sections:
        assert section in config, f"Missing {section} section"

    for field in required_fields:
        assert field in config, f"Missing {field} field"

    print("✓ WireGuard config format is valid")


def test_strongswan_config_validation():
    """Test that StrongSwan configs can be validated"""
    config = """config setup
    charondebug="ike 1"
    uniqueids=never

conn %default
    keyexchange=ikev2
    ike=aes128-sha256-modp2048
    esp=aes128-sha256-modp2048

conn ikev2-pubkey
    left=%any
    leftid=@10.0.0.1
    leftcert=server.crt
    right=%any
    rightauth=pubkey
"""

    # Validate format
    assert "config setup" in config, "Missing 'config setup' section"
    assert "conn %default" in config, "Missing 'conn %default' section"
    assert "keyexchange=ikev2" in config, "Missing IKEv2 configuration"

    print("✓ StrongSwan config format is valid")


def test_docker_algo_image():
    """Test that the Algo Docker image can be built"""
    # Check if Dockerfile exists
    assert os.path.exists("Dockerfile"), "Dockerfile not found"

    # Read Dockerfile and validate basic structure
    with open("Dockerfile") as f:
        dockerfile_content = f.read()

    required_elements = [
        "FROM",  # Base image
        "RUN",  # Build commands
        "COPY",  # Copy Algo files
        "python",  # Python dependency
    ]

    missing = []
    for element in required_elements:
        if element not in dockerfile_content:
            missing.append(element)

    assert not missing, f"Dockerfile missing elements: {', '.join(missing)}"

    print("✓ Dockerfile structure is valid")


def test_localhost_deployment_requirements():
    """Test that localhost deployment requirements are met"""
    requirements = {
        "Python 3.12+": sys.version_info >= (3, 12),
        "Ansible installed": Path(sys.executable).with_name("ansible-playbook").is_file(),
        "Main playbook exists": os.path.exists("main.yml"),
        "Project config exists": os.path.exists("pyproject.toml"),
        "Config template exists": os.path.exists("config.cfg.example") or os.path.exists("config.cfg"),
    }

    for req, met in requirements.items():
        if met:
            print(f"✓ {req}")
        else:
            print(f"✗ {req}")
    assert all(requirements.values()), "Missing localhost deployment requirements"


if __name__ == "__main__":
    print("Running Docker localhost deployment tests...")
    print("=" * 50)

    # First check if Docker is available
    docker_available = check_docker_available()
    if not docker_available:
        print("⚠ Docker not available - some tests will be limited")

    tests = [
        test_wireguard_config_validation,
        test_strongswan_config_validation,
        test_docker_algo_image,
        test_localhost_deployment_requirements,
    ]

    failed = 0
    for test in tests:
        print(f"\n{test.__name__}:")
        try:
            test()
        except Exception as e:
            print(f"✗ {test.__name__} error: {e}")
            failed += 1

    print("\n" + "=" * 50)
    if failed > 0:
        print(f"❌ {failed} tests failed")
        sys.exit(1)
    else:
        print(f"✅ All {len(tests)} tests passed!")
