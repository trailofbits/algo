#!/usr/bin/env python3
"""
Test OpenSSL compatibility across versions
Based on issues #14755, #14718 - Apple device compatibility
"""
import os
import re
import subprocess
import sys
import tempfile


def test_openssl_version_detection():
    """Test that we can detect OpenSSL version"""
    result = subprocess.run(
        ['openssl', 'version'],
        capture_output=True,
        text=True
    )

    assert result.returncode == 0, "Failed to get OpenSSL version"

    # Parse version - e.g., "OpenSSL 3.0.2 15 Mar 2022"
    version_match = re.search(r'OpenSSL\s+(\d+)\.(\d+)\.(\d+)', result.stdout)
    assert version_match, f"Can't parse OpenSSL version: {result.stdout}"

    major = int(version_match.group(1))
    minor = int(version_match.group(2))

    print(f"✓ OpenSSL version detected: {major}.{minor}")

    # Return version for other tests
    return (major, minor)


def test_legacy_flag_support():
    """Test if OpenSSL supports -legacy flag (issue #14755)"""
    major, minor = test_openssl_version_detection()

    # Test genrsa with -legacy flag
    with tempfile.NamedTemporaryFile(suffix='.key', delete=False) as f:
        temp_key = f.name

    try:
        # Try with -legacy flag
        result_legacy = subprocess.run(
            ['openssl', 'genrsa', '-legacy', '-out', temp_key, '2048'],
            capture_output=True,
            text=True
        )

        # Try without -legacy flag
        result_normal = subprocess.run(
            ['openssl', 'genrsa', '-out', temp_key, '2048'],
            capture_output=True,
            text=True
        )

        # Check which one worked
        legacy_supported = result_legacy.returncode == 0
        normal_works = result_normal.returncode == 0

        assert normal_works, "OpenSSL genrsa should work without -legacy"

        if major >= 3:
            # OpenSSL 3.x should support -legacy
            print(f"✓ OpenSSL {major}.{minor} legacy flag support: {legacy_supported}")
        else:
            # OpenSSL 1.x doesn't have -legacy flag
            assert not legacy_supported, f"OpenSSL {major}.{minor} shouldn't support -legacy"
            print(f"✓ OpenSSL {major}.{minor} correctly doesn't support -legacy")

    finally:
        if os.path.exists(temp_key):
            os.unlink(temp_key)


def test_apple_device_key_format():
    """Test key format compatibility for Apple devices"""
    # Apple devices need keys in PKCS#1 format
    with tempfile.NamedTemporaryFile(suffix='.key', delete=False) as f:
        temp_key = f.name

    try:
        # Generate a test key
        subprocess.run(
            ['openssl', 'genrsa', '-out', temp_key, '2048'],
            check=True,
            capture_output=True
        )

        # Check key format
        result = subprocess.run(
            ['openssl', 'rsa', '-in', temp_key, '-text', '-noout'],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0, "Failed to read RSA key"
        assert 'RSA Private-Key' in result.stdout or 'Private-Key' in result.stdout, \
            "Key format not recognized"

        # Test conversion to PKCS#8 (modern format)
        with tempfile.NamedTemporaryFile(suffix='.p8', delete=False) as f:
            pkcs8_key = f.name

        try:
            subprocess.run(
                ['openssl', 'pkcs8', '-topk8', '-nocrypt',
                 '-in', temp_key, '-out', pkcs8_key],
                check=True,
                capture_output=True
            )

            # Verify PKCS#8 format
            result = subprocess.run(
                ['openssl', 'pkey', '-in', pkcs8_key, '-text', '-noout'],
                capture_output=True,
                text=True
            )

            assert result.returncode == 0, "Failed to read PKCS#8 key"

        finally:
            if os.path.exists(pkcs8_key):
                os.unlink(pkcs8_key)

        print("✓ Apple device key format test passed")

    finally:
        if os.path.exists(temp_key):
            os.unlink(temp_key)


def test_certificate_compatibility():
    """Test certificate generation for different clients"""
    # Test certificate request generation
    with tempfile.NamedTemporaryFile(suffix='.csr', delete=False) as f:
        temp_csr = f.name

    with tempfile.NamedTemporaryFile(suffix='.key', delete=False) as f:
        temp_key = f.name

    try:
        # Generate key and CSR
        subprocess.run(
            ['openssl', 'genrsa', '-out', temp_key, '2048'],
            check=True,
            capture_output=True
        )

        # Create CSR with subject
        subprocess.run(
            ['openssl', 'req', '-new', '-key', temp_key,
             '-out', temp_csr, '-subj', '/CN=test-client'],
            check=True,
            capture_output=True
        )

        # Verify CSR
        result = subprocess.run(
            ['openssl', 'req', '-in', temp_csr, '-text', '-noout'],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0, "Failed to read CSR"
        assert 'CN = test-client' in result.stdout or 'CN=test-client' in result.stdout, \
            "CSR subject not found"

        print("✓ Certificate compatibility test passed")

    finally:
        for f in [temp_csr, temp_key]:
            if os.path.exists(f):
                os.unlink(f)


def test_p12_export_format():
    """Test PKCS#12 export for mobile devices"""
    # Test that we can create P12 files
    with tempfile.TemporaryDirectory() as tmpdir:
        key_file = os.path.join(tmpdir, 'test.key')
        cert_file = os.path.join(tmpdir, 'test.crt')
        p12_file = os.path.join(tmpdir, 'test.p12')

        try:
            # Generate self-signed cert for testing
            subprocess.run([
                'openssl', 'req', '-x509', '-newkey', 'rsa:2048',
                '-keyout', key_file, '-out', cert_file,
                '-days', '365', '-nodes',
                '-subj', '/CN=test-vpn-client'
            ], check=True, capture_output=True)

            # Export to P12
            result = subprocess.run([
                'openssl', 'pkcs12', '-export',
                '-in', cert_file, '-inkey', key_file,
                '-out', p12_file, '-passout', 'pass:testpass'
            ], capture_output=True, text=True)

            assert result.returncode == 0, f"P12 export failed: {result.stderr}"
            assert os.path.exists(p12_file), "P12 file not created"
            assert os.path.getsize(p12_file) > 0, "P12 file is empty"

            # Verify P12 file
            verify_result = subprocess.run([
                'openssl', 'pkcs12', '-info',
                '-in', p12_file, '-passin', 'pass:testpass',
                '-passout', 'pass:testpass'
            ], capture_output=True, text=True)

            assert verify_result.returncode == 0, "P12 verification failed"

            print("✓ PKCS#12 export format test passed")

        except subprocess.CalledProcessError as e:
            print(f"Command failed: {e.cmd}")
            print(f"Output: {e.output}")
            raise


if __name__ == "__main__":
    tests = [
        test_openssl_version_detection,
        test_legacy_flag_support,
        test_apple_device_key_format,
        test_certificate_compatibility,
        test_p12_export_format,
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
