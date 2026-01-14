#!/usr/bin/env python3
"""
Test WireGuard key generation - focused on x25519_pubkey module integration
Addresses test gap identified in tests/README.md line 63-67: WireGuard private/public key generation
"""

import base64
import os
import subprocess
import sys
import tempfile

# Add library directory to path to import our custom module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "library"))


def test_wireguard_tools_available():
    """Test that WireGuard tools are available for validation"""
    try:
        result = subprocess.run(["wg", "--version"], capture_output=True, text=True)
        assert result.returncode == 0, "WireGuard tools not available"
        print(f"✓ WireGuard tools available: {result.stdout.strip()}")
        return True
    except FileNotFoundError:
        print("⚠ WireGuard tools not available - skipping validation tests")
        return False


def test_x25519_module_import():
    """Test that our custom x25519_pubkey module can be imported and used"""
    try:
        import x25519_pubkey  # noqa: F401

        print("✓ x25519_pubkey module imports successfully")
        return True
    except ImportError as e:
        assert False, f"Cannot import x25519_pubkey module: {e}"


def generate_test_private_key():
    """Generate a test private key using the same method as Algo"""
    with tempfile.NamedTemporaryFile(suffix=".raw", delete=False) as temp_file:
        raw_key_path = temp_file.name

    try:
        # Generate 32 random bytes for X25519 private key (same as community.crypto does)
        import secrets

        raw_data = secrets.token_bytes(32)

        # Write raw key to file (like community.crypto openssl_privatekey with format: raw)
        with open(raw_key_path, "wb") as f:
            f.write(raw_data)

        assert len(raw_data) == 32, f"Private key should be 32 bytes, got {len(raw_data)}"

        b64_key = base64.b64encode(raw_data).decode()

        print(f"✓ Generated private key (base64): {b64_key[:12]}...")

        return raw_key_path, b64_key

    except Exception:
        # Clean up on error
        if os.path.exists(raw_key_path):
            os.unlink(raw_key_path)
        raise


def test_x25519_pubkey_from_raw_file():
    """Test our x25519_pubkey module with raw private key file"""
    raw_key_path, b64_key = generate_test_private_key()

    try:
        # Import here so we can mock the module_utils if needed

        # Mock the AnsibleModule for testing
        class MockModule:
            def __init__(self, params):
                self.params = params
                self.result = {}

            def fail_json(self, **kwargs):
                raise Exception(f"Module failed: {kwargs}")

            def exit_json(self, **kwargs):
                self.result = kwargs

        with tempfile.NamedTemporaryFile(suffix=".pub", delete=False) as temp_pub:
            public_key_path = temp_pub.name

        try:
            # Test the module logic directly
            import x25519_pubkey
            from x25519_pubkey import run_module

            original_AnsibleModule = x25519_pubkey.AnsibleModule

            try:
                # Mock the module call
                mock_module = MockModule(
                    {"private_key_path": raw_key_path, "public_key_path": public_key_path, "private_key_b64": None}
                )

                x25519_pubkey.AnsibleModule = lambda **kwargs: mock_module

                # Run the module
                run_module()

                # Check the result
                assert "public_key" in mock_module.result
                assert mock_module.result["changed"]
                assert os.path.exists(public_key_path)

                with open(public_key_path) as f:
                    derived_pubkey = f.read().strip()

                # Validate base64 format
                try:
                    decoded = base64.b64decode(derived_pubkey, validate=True)
                    assert len(decoded) == 32, f"Public key should be 32 bytes, got {len(decoded)}"
                except Exception as e:
                    assert False, f"Invalid base64 public key: {e}"

                print(f"✓ Derived public key from raw file: {derived_pubkey[:12]}...")

                return derived_pubkey

            finally:
                x25519_pubkey.AnsibleModule = original_AnsibleModule

        finally:
            if os.path.exists(public_key_path):
                os.unlink(public_key_path)

    finally:
        if os.path.exists(raw_key_path):
            os.unlink(raw_key_path)


def test_x25519_pubkey_from_b64_string():
    """Test our x25519_pubkey module with base64 private key string"""
    raw_key_path, b64_key = generate_test_private_key()

    try:

        class MockModule:
            def __init__(self, params):
                self.params = params
                self.result = {}

            def fail_json(self, **kwargs):
                raise Exception(f"Module failed: {kwargs}")

            def exit_json(self, **kwargs):
                self.result = kwargs

        import x25519_pubkey
        from x25519_pubkey import run_module

        original_AnsibleModule = x25519_pubkey.AnsibleModule

        try:
            mock_module = MockModule({"private_key_b64": b64_key, "private_key_path": None, "public_key_path": None})

            x25519_pubkey.AnsibleModule = lambda **kwargs: mock_module

            # Run the module
            run_module()

            # Check the result
            assert "public_key" in mock_module.result
            derived_pubkey = mock_module.result["public_key"]

            # Validate base64 format
            try:
                decoded = base64.b64decode(derived_pubkey, validate=True)
                assert len(decoded) == 32, f"Public key should be 32 bytes, got {len(decoded)}"
            except Exception as e:
                assert False, f"Invalid base64 public key: {e}"

            print(f"✓ Derived public key from base64 string: {derived_pubkey[:12]}...")

            return derived_pubkey

        finally:
            x25519_pubkey.AnsibleModule = original_AnsibleModule

    finally:
        if os.path.exists(raw_key_path):
            os.unlink(raw_key_path)


def test_wireguard_validation():
    """Test that our derived keys work with actual WireGuard tools"""
    if not test_wireguard_tools_available():
        return

    # Generate keys using our method
    raw_key_path, b64_key = generate_test_private_key()

    try:
        # Derive public key using our module

        class MockModule:
            def __init__(self, params):
                self.params = params
                self.result = {}

            def fail_json(self, **kwargs):
                raise Exception(f"Module failed: {kwargs}")

            def exit_json(self, **kwargs):
                self.result = kwargs

        import x25519_pubkey
        from x25519_pubkey import run_module

        original_AnsibleModule = x25519_pubkey.AnsibleModule

        try:
            mock_module = MockModule({"private_key_b64": b64_key, "private_key_path": None, "public_key_path": None})

            x25519_pubkey.AnsibleModule = lambda **kwargs: mock_module
            run_module()

            derived_pubkey = mock_module.result["public_key"]

        finally:
            x25519_pubkey.AnsibleModule = original_AnsibleModule

        with tempfile.NamedTemporaryFile(mode="w", suffix=".conf", delete=False) as temp_config:
            # Create a WireGuard config using our keys
            wg_config = f"""[Interface]
PrivateKey = {b64_key}
Address = 10.19.49.1/24

[Peer]
PublicKey = {derived_pubkey}
AllowedIPs = 10.19.49.2/32
"""
            temp_config.write(wg_config)
            config_path = temp_config.name

        try:
            # Test that WireGuard can parse our config
            result = subprocess.run(["wg-quick", "strip", config_path], capture_output=True, text=True)

            assert result.returncode == 0, f"WireGuard rejected our config: {result.stderr}"

            # Test key derivation with wg pubkey command
            wg_result = subprocess.run(["wg", "pubkey"], input=b64_key, capture_output=True, text=True)

            if wg_result.returncode == 0:
                wg_derived = wg_result.stdout.strip()
                assert wg_derived == derived_pubkey, f"Key mismatch: wg={wg_derived} vs ours={derived_pubkey}"
                print("✓ WireGuard validation: keys match wg pubkey output")
            else:
                print(f"⚠ Could not validate with wg pubkey: {wg_result.stderr}")

            print("✓ WireGuard accepts our generated configuration")

        finally:
            if os.path.exists(config_path):
                os.unlink(config_path)

    finally:
        if os.path.exists(raw_key_path):
            os.unlink(raw_key_path)


def test_key_consistency():
    """Test that the same private key always produces the same public key"""
    # Generate one private key to reuse
    raw_key_path, b64_key = generate_test_private_key()

    try:

        def derive_pubkey_from_same_key():
            class MockModule:
                def __init__(self, params):
                    self.params = params
                    self.result = {}

                def fail_json(self, **kwargs):
                    raise Exception(f"Module failed: {kwargs}")

                def exit_json(self, **kwargs):
                    self.result = kwargs

            import x25519_pubkey
            from x25519_pubkey import run_module

            original_AnsibleModule = x25519_pubkey.AnsibleModule

            try:
                mock_module = MockModule(
                    {
                        "private_key_b64": b64_key,  # SAME key each time
                        "private_key_path": None,
                        "public_key_path": None,
                    }
                )

                x25519_pubkey.AnsibleModule = lambda **kwargs: mock_module
                run_module()

                return mock_module.result["public_key"]

            finally:
                x25519_pubkey.AnsibleModule = original_AnsibleModule

        # Derive public key multiple times from same private key
        pubkey1 = derive_pubkey_from_same_key()
        pubkey2 = derive_pubkey_from_same_key()

        assert pubkey1 == pubkey2, f"Key derivation not consistent: {pubkey1} vs {pubkey2}"
        print("✓ Key derivation is consistent")

    finally:
        if os.path.exists(raw_key_path):
            os.unlink(raw_key_path)


if __name__ == "__main__":
    tests = [
        test_x25519_module_import,
        test_x25519_pubkey_from_raw_file,
        test_x25519_pubkey_from_b64_string,
        test_key_consistency,
        test_wireguard_validation,
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
