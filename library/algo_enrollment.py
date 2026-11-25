#!/usr/bin/python
"""Keep a controller-side record of retired device names across all VPN protocols."""

import fcntl
import json
import os
import tempfile
from pathlib import Path

from ansible.module_utils.basic import AnsibleModule
from cryptography import x509


def names(values: object) -> set[str]:
    """Read a list of single-component device names from enrollment history."""
    if not isinstance(values, list) or any(
        not isinstance(value, str) or not value or value in {".", ".."} or "/" in value or "\\" in value
        for value in values
    ):
        raise ValueError("Expected a list of device names with no path separators")
    return set(values)


def existing_devices(directory: Path) -> tuple[set[str], set[str]]:
    """Recover known devices and certificate revocations from a pre-upgrade deployment."""
    known: set[str] = set()
    retired: set[str] = set()
    pki = directory / "ipsec/.pki"
    for path in (directory / "wireguard/.pki/index.txt", pki / "all-users"):
        if path.exists():
            known.update(names(path.read_text().splitlines()))
    if (pki / "crl.pem").exists():
        crl = x509.load_pem_x509_crl((pki / "crl.pem").read_bytes())
        # Read issued certificates directly so names are never used as paths.
        revoked = {entry.serial_number for entry in crl}
        for cert_path in (pki / "certs").glob("*.crt"):
            cert = x509.load_pem_x509_certificate(cert_path.read_bytes())
            if cert.serial_number in revoked:
                retired.add(cert_path.stem)
                revoked.remove(cert.serial_number)
        if revoked:
            raise ValueError("Restore the matching client certificates before importing the existing IPsec revocations")
    return known - retired, retired


def reconcile(directory: Path, desired: list[str], *, check: bool) -> bool:
    """Reserve removed devices before any protocol can reuse their credentials."""
    requested = names(desired)
    if not directory.exists():
        if check:
            return True
        directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    path = directory / ".users.json"
    # Serialize read/replace without leaving a separate, replaceable lock file.
    lock = os.open(directory, os.O_RDONLY)
    try:
        fcntl.flock(lock, fcntl.LOCK_EX)
        state = None
        if path.exists():
            state = json.loads(path.read_text())
            if not isinstance(state, dict) or set(state) != {"active", "retired"}:
                raise ValueError(f"Restore a valid enrollment record at {path}")
            active, retired = names(state["active"]), names(state["retired"])
        else:
            active, retired = existing_devices(directory)
        retired.update(active - requested)
        reserved = {name.casefold() for name in retired}
        conflicts = sorted(name for name in requested if name.casefold() in reserved)
        if conflicts:
            raise ValueError(f"Choose a new device name for the retired enrollment(s): {', '.join(conflicts)}")
        updated = {"active": sorted(requested), "retired": sorted(retired)}
        if state == updated:
            return False
        if not check:
            with tempfile.NamedTemporaryFile(mode="w", dir=directory, delete=False) as stream:
                try:
                    json.dump(updated, stream)
                    stream.write("\n")
                    stream.flush()
                    Path(stream.name).replace(path)
                finally:
                    Path(stream.name).unlink(missing_ok=True)
        return True
    finally:
        os.close(lock)


def main() -> None:
    """Update the enrollment record on the Ansible controller."""
    module = AnsibleModule(
        argument_spec={
            "directory": {"type": "path", "required": True},
            "users": {"type": "list", "elements": "str", "required": True},
        },
        supports_check_mode=True,
    )
    try:
        changed = reconcile(Path(module.params["directory"]), module.params["users"], check=module.check_mode)
    except (OSError, ValueError) as error:
        module.fail_json(msg=str(error))
    module.exit_json(changed=changed)


if __name__ == "__main__":
    main()
