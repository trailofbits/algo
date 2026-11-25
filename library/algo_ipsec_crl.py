#!/usr/bin/python
"""Sign the IPsec revocation list with the issuer identifier used by strongSwan."""

from datetime import UTC, datetime, timedelta
from pathlib import Path

from ansible.module_utils.basic import AnsibleModule
from cryptography import x509
from cryptography.exceptions import InvalidSignature, UnsupportedAlgorithm
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec, rsa

DOCUMENTATION = """
module: algo_ipsec_crl
short_description: Sign a revocation list for an Algo IPsec server
description: Uses the saved CA and client certificates to produce a CRL that strongSwan can match to its issuer.
options:
  pki_dir:
    description: Directory containing the deployment CA and issued certificates.
    type: path
    required: true
  revoked_users:
    description: Certificate holders whose access has been removed.
    type: list
    elements: str
    required: true
  ca_password:
    description: Password for the encrypted CA private key.
    type: str
    required: true
"""


def build_crl(pki: Path, users: list[str], password: str, now: datetime) -> bytes | None:
    """Build an issuer-bound CRL, preserving existing revocation dates.

    Args:
        pki: Directory containing the deployment CA and issued certificates.
        users: Names of certificate holders whose access has been removed.
        password: Password for the encrypted CA key.
        now: Current time in UTC.

    Returns:
        A signed PEM list, or None when the installed list is current.

    Raises:
        OSError: A required certificate or key cannot be read.
        ValueError: The saved credentials are invalid or belong to another CA.
    """
    ca = x509.load_pem_x509_certificate((pki / "cacert.pem").read_bytes())
    key = serialization.load_pem_private_key((pki / "private/cakey.pem").read_bytes(), password.encode())
    if not isinstance(key, (ec.EllipticCurvePrivateKey, rsa.RSAPrivateKey)) or key.public_key() != ca.public_key():
        raise ValueError("The CA certificate and private key must belong to the same deployment")
    try:
        subject_id = ca.extensions.get_extension_for_class(x509.SubjectKeyIdentifier).value
    except x509.ExtensionNotFound:
        subject_id = x509.SubjectKeyIdentifier.from_public_key(key.public_key())
    issuer_id = x509.AuthorityKeyIdentifier.from_issuer_subject_key_identifier(subject_id)

    serials = set()
    for user in users:
        if user in ("", ".", "..") or Path(user).name != user:
            raise ValueError(f"Expected a certificate holder's name, got {user!r}")
        certificate = x509.load_pem_x509_certificate((pki / "certs" / f"{user}.crt").read_bytes())
        certificate.verify_directly_issued_by(ca)
        serials.add(certificate.serial_number)

    entries = {}
    number = 0
    path = pki / "crl.pem"
    if path.exists():
        old = x509.load_pem_x509_crl(path.read_bytes())
        if old.issuer != ca.subject or not old.is_signature_valid(key.public_key()):
            raise ValueError("Restore the revocation list signed by this deployment's CA")
        entries = {entry.serial_number: entry for entry in old}
        extensions = {ext.oid: ext.value for ext in old.extensions}
        old_number = extensions.get(x509.ExtensionOID.CRL_NUMBER)
        if isinstance(old_number, x509.CRLNumber):
            number = old_number.crl_number
        if (
            number > 0
            and extensions.get(x509.ExtensionOID.AUTHORITY_KEY_IDENTIFIER) == issuer_id
            and entries.keys() == serials
            and old.last_update_utc <= now
            and old.next_update_utc is not None
            and old.next_update_utc > now + timedelta(days=1)
        ):
            return None

    builder = (
        x509.CertificateRevocationListBuilder()
        .issuer_name(ca.subject)
        .last_update(now)
        .next_update(now + timedelta(days=3650))
        .add_extension(issuer_id, critical=False)
        .add_extension(x509.CRLNumber(number + 1), critical=False)
    )
    for serial in sorted(serials):
        entry = entries.get(serial)
        if entry is None:
            entry = x509.RevokedCertificateBuilder().serial_number(serial).revocation_date(now).build()
        builder = builder.add_revoked_certificate(entry)
    return builder.sign(key, hashes.SHA256()).public_bytes(serialization.Encoding.PEM)


def main() -> None:
    """Generate the deployment CRL and replace the saved file atomically."""
    module = AnsibleModule(
        argument_spec={
            "pki_dir": {"type": "path", "required": True},
            "revoked_users": {"type": "list", "elements": "str", "required": True},
            "ca_password": {"type": "str", "required": True, "no_log": True},
        },
        supports_check_mode=True,
    )
    pki = Path(module.params["pki_dir"])
    try:
        content = build_crl(pki, module.params["revoked_users"], module.params["ca_password"], datetime.now(UTC))
        if content is not None and not module.check_mode:
            temporary = Path(module.tmpdir) / "crl.pem"
            temporary.write_bytes(content)
            module.atomic_move(str(temporary), str(pki / "crl.pem"))
    except (OSError, ValueError, TypeError, InvalidSignature, UnsupportedAlgorithm) as error:
        module.fail_json(msg=f"Cannot generate the IPsec revocation list in {pki}: {error}")
    module.exit_json(changed=content is not None)


if __name__ == "__main__":
    main()
