#!/usr/bin/python
"""Derive WireGuard public keys from raw or base64-encoded X25519 private keys."""

import base64
import binascii
from pathlib import Path

from ansible.module_utils.basic import AnsibleModule
from cryptography.hazmat.primitives.asymmetric import x25519


def read_private_key(private_key_path: str | None, private_key_b64: str | None) -> bytes:
    """Read a 32-byte private key without stripping bytes from raw input.

    Args:
        private_key_path: File containing a raw key or base64 text.
        private_key_b64: Base64 text used when no file is specified.

    Returns:
        The raw private key.

    Raises:
        ValueError: The file cannot be read or the key is malformed.
    """
    if private_key_path:
        try:
            data = Path(private_key_path).read_bytes()
        except OSError as error:
            raise ValueError(f"Cannot read private key {private_key_path}: {error}") from error
        if len(data) == 32:
            return data
        encoded = data.strip()
    else:
        encoded = private_key_b64 or ""

    try:
        key = base64.b64decode(encoded, validate=True)
    except (binascii.Error, ValueError) as error:
        raise ValueError("Invalid private key: supply base64 text or a 32-byte raw file") from error
    if len(key) != 32:
        raise ValueError(f"Private key must decode to exactly 32 bytes; got {len(key)}")
    return key


def write_public_key(path: str, public_key: str, *, check_mode: bool) -> bool:
    """Write a changed public key, respecting Ansible's check mode.

    Args:
        path: Destination file.
        public_key: Base64-encoded public key.
        check_mode: Report the expected change without writing the file.

    Returns:
        Whether the file differs from the derived public key.

    Raises:
        ValueError: The destination cannot be read or written.
    """
    destination = Path(path)
    try:
        existing = destination.read_text().strip()
    except FileNotFoundError:
        existing = None
    except (OSError, UnicodeError) as error:
        raise ValueError(f"Cannot read public key {path}: {error}") from error
    if existing == public_key:
        return False
    if not check_mode:
        try:
            destination.write_text(public_key)
        except OSError as error:
            raise ValueError(f"Cannot write public key {path}: {error}") from error
    return True


def run_module() -> None:
    """Validate Ansible arguments and return the derived public key."""
    module = AnsibleModule(
        argument_spec={
            "private_key_b64": {"type": "str", "no_log": True},
            "private_key_path": {"type": "path"},
            "public_key_path": {"type": "path"},
        },
        required_one_of=[["private_key_b64", "private_key_path"]],
        supports_check_mode=True,
    )
    try:
        key = read_private_key(module.params["private_key_path"], module.params["private_key_b64"])
        public_key = base64.b64encode(
            x25519.X25519PrivateKey.from_private_bytes(key).public_key().public_bytes_raw()
        ).decode()
        result = {"changed": False, "public_key": public_key}
        if path := module.params["public_key_path"]:
            result["changed"] = write_public_key(path, public_key, check_mode=module.check_mode)
            result["public_key_path"] = path
    except ValueError as error:
        module.fail_json(msg=str(error))
    module.exit_json(**result)


if __name__ == "__main__":
    run_module()
