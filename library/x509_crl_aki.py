#!/usr/bin/python
"""Generate an X.509 CRL with the AKI StrongSwan needs for strict lookup."""

from __future__ import annotations

import os
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

from ansible.module_utils.basic import AnsibleModule
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization


def build_crl(
    *,
    ca_certificate: x509.Certificate,
    ca_private_key: Any,
    last_update: datetime,
    next_update: datetime,
    revoked: list[tuple[int, datetime]],
) -> x509.CertificateRevocationList:
    """Build and sign a CRL whose AKI matches the issuing CA's SKI."""
    ca_public = ca_certificate.public_key().public_bytes(
        serialization.Encoding.DER, serialization.PublicFormat.SubjectPublicKeyInfo
    )
    key_public = ca_private_key.public_key().public_bytes(
        serialization.Encoding.DER, serialization.PublicFormat.SubjectPublicKeyInfo
    )
    if ca_public != key_public:
        raise ValueError("CA private key does not match CA certificate")
    builder = (
        x509.CertificateRevocationListBuilder()
        .issuer_name(ca_certificate.subject)
        .last_update(last_update)
        .next_update(next_update)
    )
    try:
        ski = ca_certificate.extensions.get_extension_for_class(x509.SubjectKeyIdentifier).value
        aki = x509.AuthorityKeyIdentifier.from_issuer_subject_key_identifier(ski)
    except x509.ExtensionNotFound:
        aki = x509.AuthorityKeyIdentifier.from_issuer_public_key(cast(Any, ca_certificate.public_key()))
    builder = builder.add_extension(aki, critical=False)

    for serial_number, revocation_date in revoked:
        entry = x509.RevokedCertificateBuilder().serial_number(serial_number).revocation_date(revocation_date).build()
        builder = builder.add_revoked_certificate(entry)

    return builder.sign(private_key=ca_private_key, algorithm=hashes.SHA256())


def crl_matches(
    crl: x509.CertificateRevocationList,
    *,
    ca_certificate: x509.Certificate,
    last_update: datetime,
    next_update: datetime,
    revoked: list[tuple[int, datetime]],
) -> bool:
    """Return whether an existing CRL already represents the requested state."""
    try:
        ca_ski = ca_certificate.extensions.get_extension_for_class(x509.SubjectKeyIdentifier).value.digest
        crl_aki = crl.extensions.get_extension_for_class(x509.AuthorityKeyIdentifier).value.key_identifier
        actual_revoked = sorted((entry.serial_number, entry.revocation_date_utc) for entry in crl)
        expected_revoked = sorted(revoked)
        return (
            crl.issuer == ca_certificate.subject
            and crl_aki == ca_ski
            and crl.last_update_utc == last_update
            and crl.next_update_utc == next_update
            and actual_revoked == expected_revoked
            and crl.signature_hash_algorithm is not None
            and crl.signature_hash_algorithm.name == "sha256"
            and crl.is_signature_valid(cast(Any, ca_certificate.public_key()))
        )
    except (ValueError, x509.ExtensionNotFound):
        return False


def _parse_timestamp(value: str) -> datetime:
    return datetime.strptime(value, "%Y%m%d%H%M%SZ").replace(tzinfo=UTC)


def _read_certificate(path: str) -> x509.Certificate:
    return x509.load_pem_x509_certificate(Path(path).read_bytes())


def main() -> None:
    module = AnsibleModule(
        argument_spec={
            "path": {"type": "path", "required": True},
            "ca_certificate_path": {"type": "path", "required": True},
            "privatekey_path": {"type": "path", "required": True},
            "privatekey_passphrase": {"type": "str", "required": True, "no_log": True},
            "last_update": {"type": "str", "required": True},
            "next_update": {"type": "str", "required": True},
            "revoked_certificates": {
                "type": "list",
                "elements": "dict",
                "default": [],
                "options": {
                    "path": {"type": "path", "required": True},
                    "revocation_date": {"type": "str", "required": True},
                },
            },
            "mode": {"type": "str", "default": "0644"},
        },
        supports_check_mode=True,
    )

    try:
        ca_certificate = _read_certificate(module.params["ca_certificate_path"])
        private_key = serialization.load_pem_private_key(
            Path(module.params["privatekey_path"]).read_bytes(),
            password=module.params["privatekey_passphrase"].encode(),
        )
        revoked = [
            (_read_certificate(item["path"]).serial_number, _parse_timestamp(item["revocation_date"]))
            for item in module.params["revoked_certificates"]
        ]
        last_update = _parse_timestamp(module.params["last_update"])
        next_update = _parse_timestamp(module.params["next_update"])
        destination = Path(module.params["path"])
        existing_crl = None
        if destination.exists():
            try:
                existing_crl = x509.load_pem_x509_crl(destination.read_bytes())
            except ValueError:
                existing_crl = None
        changed = existing_crl is None or not crl_matches(
            existing_crl,
            ca_certificate=ca_certificate,
            last_update=last_update,
            next_update=next_update,
            revoked=revoked,
        )

        content = b""
        if changed:
            crl = build_crl(
                ca_certificate=ca_certificate,
                ca_private_key=private_key,
                last_update=last_update,
                next_update=next_update,
                revoked=revoked,
            )
            content = crl.public_bytes(serialization.Encoding.PEM)

        if changed and not module.check_mode:
            destination.parent.mkdir(parents=True, exist_ok=True)
            descriptor, temporary = tempfile.mkstemp(dir=destination.parent, prefix=f".{destination.name}.")
            try:
                with os.fdopen(descriptor, "wb") as handle:
                    handle.write(content)
                    handle.flush()
                    os.fsync(handle.fileno())
                os.chmod(temporary, int(module.params["mode"], 8))
                os.replace(temporary, destination)
            finally:
                if os.path.exists(temporary):
                    os.unlink(temporary)
        elif destination.exists() and not module.check_mode:
            os.chmod(destination, int(module.params["mode"], 8))

        module.exit_json(changed=changed, path=str(destination))
    except Exception as error:
        module.fail_json(msg=f"failed to generate AKI-bearing CRL: {error}")


if __name__ == "__main__":
    main()
