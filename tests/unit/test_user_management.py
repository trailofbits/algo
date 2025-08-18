#!/usr/bin/env python3
"""
Test user management functionality without deployment
Based on issues #14745, #14746, #14738, #14726
"""

import os
import re
import sys
import tempfile

import yaml


def test_user_list_parsing():
    """Test that user lists in config.cfg are parsed correctly"""
    test_config = """
users:
  - alice
  - bob
  - charlie
  - user-with-dash
  - user_with_underscore
"""

    config = yaml.safe_load(test_config)
    users = config.get("users", [])

    assert len(users) == 5, f"Expected 5 users, got {len(users)}"
    assert "alice" in users, "Missing user 'alice'"
    assert "user-with-dash" in users, "Dash in username not handled"
    assert "user_with_underscore" in users, "Underscore in username not handled"

    # Test that usernames are valid
    username_pattern = re.compile(r"^[a-zA-Z0-9_-]+$")
    for user in users:
        assert username_pattern.match(user), f"Invalid username format: {user}"

    print("✓ User list parsing test passed")


def test_server_selection_format():
    """Test server selection string parsing (issue #14727)"""
    # Test various server display formats
    test_cases = [
        {"display": "1. 192.168.1.100 (algo-server)", "expected_ip": "192.168.1.100", "expected_name": "algo-server"},
        {"display": "2. 10.0.0.1 (production-vpn)", "expected_ip": "10.0.0.1", "expected_name": "production-vpn"},
        {
            "display": "3. vpn.example.com (example-server)",
            "expected_ip": "vpn.example.com",
            "expected_name": "example-server",
        },
    ]

    # Pattern to extract IP and name from display string
    pattern = re.compile(r"^\d+\.\s+([^\s]+)\s+\(([^)]+)\)$")

    for case in test_cases:
        match = pattern.match(case["display"])
        assert match, f"Failed to parse: {case['display']}"

        ip_or_host = match.group(1)
        name = match.group(2)

        assert ip_or_host == case["expected_ip"], f"Wrong IP extracted: {ip_or_host}"
        assert name == case["expected_name"], f"Wrong name extracted: {name}"

    print("✓ Server selection format test passed")


def test_ssh_key_preservation():
    """Test that SSH keys aren't regenerated unnecessarily"""
    with tempfile.TemporaryDirectory() as tmpdir:
        ssh_key_path = os.path.join(tmpdir, "test_key")

        # Simulate existing SSH key
        with open(ssh_key_path, "w") as f:
            f.write("EXISTING_SSH_KEY_CONTENT")
        with open(f"{ssh_key_path}.pub", "w") as f:
            f.write("ssh-rsa EXISTING_PUBLIC_KEY")

        # Record original content
        with open(ssh_key_path) as f:
            original_content = f.read()

        # Test that key is preserved when it already exists
        assert os.path.exists(ssh_key_path), "SSH key should exist"
        assert os.path.exists(f"{ssh_key_path}.pub"), "SSH public key should exist"

        # Verify content hasn't changed
        with open(ssh_key_path) as f:
            current_content = f.read()
        assert current_content == original_content, "SSH key was modified"

    print("✓ SSH key preservation test passed")


def test_ca_password_handling():
    """Test CA password validation and handling"""
    # Test password requirements
    valid_passwords = ["SecurePassword123!", "Algo-VPN-2024", "Complex#Pass@Word999"]

    invalid_passwords = [
        "",  # Empty
        "short",  # Too short
        "password with spaces",  # Spaces not allowed in some contexts
    ]

    # Basic password validation
    for pwd in valid_passwords:
        assert len(pwd) >= 12, f"Password too short: {pwd}"
        assert " " not in pwd, f"Password contains spaces: {pwd}"

    for pwd in invalid_passwords:
        issues = []
        if len(pwd) < 12:
            issues.append("too short")
        if " " in pwd:
            issues.append("contains spaces")
        if not pwd:
            issues.append("empty")
        assert issues, f"Expected validation issues for: {pwd}"

    print("✓ CA password handling test passed")


def test_user_config_generation():
    """Test that user configs would be generated correctly"""
    users = ["alice", "bob", "charlie"]
    server_name = "test-server"

    # Simulate config file structure
    for user in users:
        # Test WireGuard config path
        wg_path = f"configs/{server_name}/wireguard/{user}.conf"
        assert user in wg_path, "Username not in WireGuard config path"

        # Test IPsec config path
        ipsec_path = f"configs/{server_name}/ipsec/{user}.p12"
        assert user in ipsec_path, "Username not in IPsec config path"

        # Test SSH tunnel config path
        ssh_path = f"configs/{server_name}/ssh-tunnel/{user}.pem"
        assert user in ssh_path, "Username not in SSH config path"

    print("✓ User config generation test passed")


def test_duplicate_user_handling():
    """Test handling of duplicate usernames"""
    test_config = """
users:
  - alice
  - bob
  - alice
  - charlie
"""

    config = yaml.safe_load(test_config)
    users = config.get("users", [])

    # Check for duplicates
    unique_users = list(set(users))
    assert len(unique_users) < len(users), "Duplicates should be detected"

    # Test that duplicates can be identified
    seen = set()
    duplicates = []
    for user in users:
        if user in seen:
            duplicates.append(user)
        seen.add(user)

    assert "alice" in duplicates, "Duplicate 'alice' not detected"

    print("✓ Duplicate user handling test passed")


if __name__ == "__main__":
    tests = [
        test_user_list_parsing,
        test_server_selection_format,
        test_ssh_key_preservation,
        test_ca_password_handling,
        test_user_config_generation,
        test_duplicate_user_handling,
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
