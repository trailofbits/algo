#!/usr/bin/env python3
"""
Test OpenSSL compatibility - focused on version detection and legacy flag support
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


if __name__ == "__main__":
    tests = [
        test_openssl_version_detection,
        test_legacy_flag_support,
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