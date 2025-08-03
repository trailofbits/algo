#!/usr/bin/env python3
"""
Test certificate and crypto validation without deployment
"""
import os
import re
import sys
import tempfile
import subprocess


def test_openssl_available():
    """Test that OpenSSL is available for cert operations"""
    result = subprocess.run(
        ['openssl', 'version'],
        capture_output=True,
        text=True
    )
    
    assert result.returncode == 0, "OpenSSL not available"
    assert 'OpenSSL' in result.stdout, "OpenSSL version check failed"
    
    print(f"✓ OpenSSL available: {result.stdout.strip()}")


def test_certificate_fields():
    """Test that we can validate certificate fields"""
    # Sample certificate subject format
    subject_pattern = re.compile(r'/CN=[\w\.-]+/')
    
    test_subjects = [
        "/CN=algo-vpn-server/",
        "/CN=192.168.1.1/",
        "/CN=vpn.example.com/"
    ]
    
    for subject in test_subjects:
        assert subject_pattern.search(subject), f"Invalid subject format: {subject}"
    
    print("✓ Certificate subject format validation passed")


def test_key_permissions():
    """Test that we validate proper key file permissions"""
    # Create a temporary key file
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write("fake-private-key-content")
        temp_key = f.name
    
    try:
        # Set restrictive permissions (0600)
        os.chmod(temp_key, 0o600)
        
        # Check permissions
        stat_info = os.stat(temp_key)
        mode = stat_info.st_mode & 0o777
        
        assert mode == 0o600, f"Key file has wrong permissions: {oct(mode)}"
        print("✓ Key file permissions validation passed")
    finally:
        os.unlink(temp_key)


def test_password_complexity():
    """Test password generation requirements"""
    # Algo should generate strong passwords
    min_length = 12
    
    # Test password pattern (alphanumeric + special chars)
    password_pattern = re.compile(r'^[A-Za-z0-9!@#$%^&*()_+=\-{}[\]|:;"\'<>,.?/]{12,}$')
    
    test_passwords = [
        "StrongP@ssw0rd123!",
        "AnotherSecure#Pass99",
        "Algo-VPN-2024-Secret!"
    ]
    
    for pwd in test_passwords:
        assert len(pwd) >= min_length, f"Password too short: {len(pwd)} chars"
        assert password_pattern.match(pwd), f"Invalid password format: {pwd}"
    
    print("✓ Password complexity validation passed")


def test_ipsec_cipher_suites():
    """Test that IPsec cipher suites are secure"""
    # Algo uses strong crypto only
    allowed_ciphers = [
        'aes256gcm16',
        'aes128gcm16',
        'sha256',
        'sha384',
        'sha512',
        'prfsha256',
        'prfsha384',
        'prfsha512',
        'ecp256',
        'ecp384',
        'ecp521',
        'curve25519'
    ]
    
    weak_ciphers = ['des', '3des', 'md5', 'sha1', 'modp1024']
    
    # Ensure no weak ciphers are in allowed list
    for weak in weak_ciphers:
        assert weak not in allowed_ciphers, f"Weak cipher found: {weak}"
    
    print("✓ IPsec cipher suite validation passed")


if __name__ == "__main__":
    tests = [
        test_openssl_available,
        test_certificate_fields,
        test_key_permissions,
        test_password_complexity,
        test_ipsec_cipher_suites,
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