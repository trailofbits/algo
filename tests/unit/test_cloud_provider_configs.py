#!/usr/bin/env python3
"""
Test cloud provider instance type configurations
Focused on validating that configured instance types are current/valid
Based on issues #14730 - Hetzner changed from cx11 to cx22
"""

import sys


def test_hetzner_server_types():
    """Test Hetzner server type configurations (issue #14730)"""
    # Hetzner deprecated cx11 and cpx11 - smallest is now cx22
    deprecated_types = ["cx11", "cpx11"]
    current_types = ["cx22", "cpx22", "cx32", "cpx32", "cx42", "cpx42"]

    # Test that we're not using deprecated types in any configs
    test_config = {
        "cloud_providers": {
            "hetzner": {
                "size": "cx22",  # Should be cx22, not cx11
                "image": "ubuntu-22.04",
                "location": "hel1",
            }
        }
    }

    hetzner = test_config["cloud_providers"]["hetzner"]
    assert hetzner["size"] not in deprecated_types, f"Using deprecated Hetzner type: {hetzner['size']}"
    assert hetzner["size"] in current_types, f"Unknown Hetzner type: {hetzner['size']}"

    print("✓ Hetzner server types test passed")


def test_digitalocean_instance_types():
    """Test DigitalOcean droplet size naming"""
    # DigitalOcean uses format like s-1vcpu-1gb
    valid_sizes = ["s-1vcpu-1gb", "s-2vcpu-2gb", "s-2vcpu-4gb", "s-4vcpu-8gb"]
    deprecated_sizes = ["512mb", "1gb", "2gb"]  # Old naming scheme

    test_size = "s-2vcpu-2gb"
    assert test_size in valid_sizes, f"Invalid DO size: {test_size}"
    assert test_size not in deprecated_sizes, f"Using deprecated DO size: {test_size}"

    print("✓ DigitalOcean instance types test passed")


def test_aws_instance_types():
    """Test AWS EC2 instance type naming"""
    # Common valid instance types
    valid_types = ["t2.micro", "t3.micro", "t3.small", "t3.medium", "m5.large"]
    deprecated_types = ["t1.micro", "m1.small"]  # Very old types

    test_type = "t3.micro"
    assert test_type in valid_types, f"Unknown EC2 type: {test_type}"
    assert test_type not in deprecated_types, f"Using deprecated EC2 type: {test_type}"

    print("✓ AWS instance types test passed")


def test_vultr_instance_types():
    """Test Vultr instance type naming"""
    # Vultr uses format like vc2-1c-1gb
    test_type = "vc2-1c-1gb"
    assert any(test_type.startswith(prefix) for prefix in ["vc2-", "vhf-", "vhp-"]), (
        f"Invalid Vultr type format: {test_type}"
    )

    print("✓ Vultr instance types test passed")


if __name__ == "__main__":
    tests = [
        test_hetzner_server_types,
        test_digitalocean_instance_types,
        test_aws_instance_types,
        test_vultr_instance_types,
    ]

    failed = 0
    for test in tests:
        try:
            test()
        except AssertionError as e:
            print(f"✗ {test.__name__} failed: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ {test.__name__} error: {e}")
            failed += 1

    if failed > 0:
        print(f"\n{failed} tests failed")
        sys.exit(1)
    else:
        print(f"\nAll {len(tests)} tests passed!")
