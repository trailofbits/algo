#!/usr/bin/python

# x25519_pubkey.py - Ansible module to derive a base64-encoded WireGuard-compatible public key
# from a base64-encoded 32-byte X25519 private key.
#
# Why: community.crypto does not provide raw public key derivation for X25519 keys.

import base64

from ansible.module_utils.basic import AnsibleModule
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import x25519

"""
Ansible module to derive base64-encoded X25519 public keys from private keys.

Supports both base64-encoded strings and raw 32-byte key files.
Used for WireGuard key generation where community.crypto lacks raw public key derivation.

Parameters:
- private_key_b64: Base64-encoded X25519 private key string
- private_key_path: Path to file containing X25519 private key (base64 or raw 32 bytes)
- public_key_path: Path where the derived public key should be written

Returns:
- public_key: Base64-encoded X25519 public key
- changed: Whether the public key file was modified
- public_key_path: Path where public key was written (if specified)
"""


def run_module():
    """
    Main execution function for the x25519_pubkey Ansible module.

    Handles parameter validation, private key processing, public key derivation,
    and optional file output with idempotent behavior.
    """
    module_args = {
        "private_key_b64": {"type": "str", "required": False},
        "private_key_path": {"type": "path", "required": False},
        "public_key_path": {"type": "path", "required": False},
    }

    result = {
        "changed": False,
        "public_key": "",
    }

    module = AnsibleModule(
        argument_spec=module_args, required_one_of=[["private_key_b64", "private_key_path"]], supports_check_mode=True
    )

    priv_b64 = None

    if module.params["private_key_path"]:
        try:
            with open(module.params["private_key_path"], "rb") as f:
                data = f.read()
            try:
                # First attempt: assume file contains base64 text data
                # Strip whitespace from edges for text files (safe for base64 strings)
                stripped_data = data.strip()
                base64.b64decode(stripped_data, validate=True)
                priv_b64 = stripped_data.decode()
            except (base64.binascii.Error, ValueError):
                # Second attempt: assume file contains raw binary data
                # CRITICAL: Do NOT strip raw binary data - X25519 keys can contain
                # whitespace-like bytes (0x09, 0x0A, etc.) that must be preserved
                # Stripping would corrupt the key and cause "got 31 bytes" errors
                if len(data) != 32:
                    module.fail_json(
                        msg=f"Private key file must be either base64 or exactly 32 raw bytes, got {len(data)} bytes"
                    )
                priv_b64 = base64.b64encode(data).decode()
        except OSError as e:
            module.fail_json(msg=f"Failed to read private key file: {e}")
    else:
        priv_b64 = module.params["private_key_b64"]

    # Validate input parameters
    if not priv_b64:
        module.fail_json(msg="No private key provided")

    try:
        priv_raw = base64.b64decode(priv_b64, validate=True)
    except Exception as e:
        module.fail_json(msg=f"Invalid base64 private key format: {e}")

    if len(priv_raw) != 32:
        module.fail_json(msg=f"Private key must decode to exactly 32 bytes, got {len(priv_raw)}")

    try:
        priv_key = x25519.X25519PrivateKey.from_private_bytes(priv_raw)
        pub_key = priv_key.public_key()
        pub_raw = pub_key.public_bytes(encoding=serialization.Encoding.Raw, format=serialization.PublicFormat.Raw)
        pub_b64 = base64.b64encode(pub_raw).decode()
        result["public_key"] = pub_b64

        if module.params["public_key_path"]:
            pub_path = module.params["public_key_path"]
            existing = None

            try:
                with open(pub_path) as f:
                    existing = f.read().strip()
            except OSError:
                existing = None

            if existing != pub_b64:
                try:
                    with open(pub_path, "w") as f:
                        f.write(pub_b64)
                    result["changed"] = True
                except OSError as e:
                    module.fail_json(msg=f"Failed to write public key file: {e}")

            result["public_key_path"] = pub_path

    except Exception as e:
        module.fail_json(msg=f"Failed to derive public key: {e}")

    module.exit_json(**result)


def main():
    """Entry point when module is executed directly."""
    run_module()


if __name__ == "__main__":
    main()
