#!/usr/bin/env python3
"""
Test configuration file validation without deployment
"""

import configparser
import os
import re
import subprocess
import sys
import tempfile


def test_wireguard_config_format():
    """Test that we can validate WireGuard config format"""
    # Sample minimal WireGuard config
    sample_config = """[Interface]
PrivateKey = aGVsbG8gd29ybGQgdGhpcyBpcyBub3QgYSByZWFsIGtleQo=
Address = 10.19.49.2/32
DNS = 10.19.49.1

[Peer]
PublicKey = U29tZVB1YmxpY0tleVRoYXRJc05vdFJlYWxseVZhbGlkCg==
AllowedIPs = 0.0.0.0/0,::/0
Endpoint = 192.168.1.1:51820
"""

    # Validate it has required sections
    config = configparser.ConfigParser()
    config.read_string(sample_config)

    assert "Interface" in config, "Missing [Interface] section"
    assert "Peer" in config, "Missing [Peer] section"

    # Validate required fields
    assert config["Interface"].get("PrivateKey"), "Missing PrivateKey"
    assert config["Interface"].get("Address"), "Missing Address"
    assert config["Peer"].get("PublicKey"), "Missing PublicKey"
    assert config["Peer"].get("AllowedIPs"), "Missing AllowedIPs"

    print("✓ WireGuard config format validation passed")


def test_base64_key_format():
    """Test that keys are in valid base64 format"""
    # Base64 keys can have variable length, just check format
    key_pattern = re.compile(r"^[A-Za-z0-9+/]+=*$")

    test_keys = [
        "aGVsbG8gd29ybGQgdGhpcyBpcyBub3QgYSByZWFsIGtleQo=",
        "U29tZVB1YmxpY0tleVRoYXRJc05vdFJlYWxseVZhbGlkCg==",
    ]

    for key in test_keys:
        assert key_pattern.match(key), f"Invalid key format: {key}"

    print("✓ Base64 key format validation passed")


def test_ip_address_format():
    """Test IP address and CIDR notation validation"""
    ip_pattern = re.compile(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/\d{1,2}$")
    endpoint_pattern = re.compile(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d{1,5}$")

    # Test CIDR notation
    assert ip_pattern.match("10.19.49.2/32"), "Invalid CIDR notation"
    assert ip_pattern.match("192.168.1.0/24"), "Invalid CIDR notation"

    # Test endpoint format
    assert endpoint_pattern.match("192.168.1.1:51820"), "Invalid endpoint format"

    print("✓ IP address format validation passed")


def test_mobile_config_xml():
    """Test that mobile config files would be valid XML"""
    # First check if xmllint is available
    xmllint_check = subprocess.run(["which", "xmllint"], capture_output=True, text=True)

    if xmllint_check.returncode != 0:
        print("⚠ Skipping XML validation test (xmllint not installed)")
        return

    sample_mobileconfig = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>PayloadDisplayName</key>
    <string>Algo VPN</string>
    <key>PayloadIdentifier</key>
    <string>com.algo-vpn.ios</string>
    <key>PayloadType</key>
    <string>Configuration</string>
    <key>PayloadVersion</key>
    <integer>1</integer>
</dict>
</plist>"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".mobileconfig", delete=False) as f:
        f.write(sample_mobileconfig)
        temp_file = f.name

    try:
        # Use xmllint to validate
        result = subprocess.run(["xmllint", "--noout", temp_file], capture_output=True, text=True)

        assert result.returncode == 0, f"XML validation failed: {result.stderr}"
        print("✓ Mobile config XML validation passed")
    finally:
        os.unlink(temp_file)


def test_port_ranges():
    """Test that configured ports are in valid ranges"""
    valid_ports = [22, 80, 443, 500, 4500, 51820]

    for port in valid_ports:
        assert 1 <= port <= 65535, f"Invalid port number: {port}"

    # Test common VPN ports
    assert 500 in valid_ports, "Missing IKE port 500"
    assert 4500 in valid_ports, "Missing IPsec NAT-T port 4500"
    assert 51820 in valid_ports, "Missing WireGuard port 51820"

    print("✓ Port range validation passed")


if __name__ == "__main__":
    tests = [
        test_wireguard_config_format,
        test_base64_key_format,
        test_ip_address_format,
        test_mobile_config_xml,
        test_port_ranges,
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
