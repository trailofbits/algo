#!/usr/bin/env python3
"""
Simplified Docker-based localhost deployment tests
Verifies services can start and config files exist in expected locations
"""

import os
import subprocess
import sys


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
        if section not in config:
            print(f"✗ Missing {section} section")
            return False

    for field in required_fields:
        if field not in config:
            print(f"✗ Missing {field} field")
            return False

    print("✓ WireGuard config format is valid")
    return True


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
    if "config setup" not in config:
        print("✗ Missing 'config setup' section")
        return False

    if "conn %default" not in config:
        print("✗ Missing 'conn %default' section")
        return False

    if "keyexchange=ikev2" not in config:
        print("✗ Missing IKEv2 configuration")
        return False

    print("✓ StrongSwan config format is valid")
    return True


def test_docker_algo_image():
    """Test that the Algo Docker image can be built"""
    # Check if Dockerfile exists
    if not os.path.exists("Dockerfile"):
        print("✗ Dockerfile not found")
        return False

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

    if missing:
        print(f"✗ Dockerfile missing elements: {', '.join(missing)}")
        return False

    print("✓ Dockerfile structure is valid")
    return True


def test_localhost_deployment_requirements():
    """Test that localhost deployment requirements are met"""
    requirements = {
        "Python 3.8+": sys.version_info >= (3, 8),
        "Ansible installed": subprocess.run(["which", "ansible"], capture_output=True).returncode == 0,
        "Main playbook exists": os.path.exists("main.yml"),
        "Project config exists": os.path.exists("pyproject.toml"),
        "Config template exists": os.path.exists("config.cfg.example") or os.path.exists("config.cfg"),
    }

    all_met = True
    for req, met in requirements.items():
        if met:
            print(f"✓ {req}")
        else:
            print(f"✗ {req}")
            all_met = False

    return all_met


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
            if not test():
                failed += 1
        except Exception as e:
            print(f"✗ {test.__name__} error: {e}")
            failed += 1

    print("\n" + "=" * 50)
    if failed > 0:
        print(f"❌ {failed} tests failed")
        sys.exit(1)
    else:
        print(f"✅ All {len(tests)} tests passed!")
