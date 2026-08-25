"""CRL generation contract required by StrongSwan strict revocation."""

import importlib.util
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from cryptography import x509
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.x509.oid import NameOID

ROOT = Path(__file__).parents[2]
MODULE_PATH = ROOT / "library/x509_crl_aki.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("x509_crl_aki", MODULE_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _certificate(subject: x509.Name, issuer: x509.Name, public_key, issuer_key, *, ca: bool):
    now = datetime.now(UTC).replace(microsecond=0)
    builder = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(public_key)
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - timedelta(minutes=1))
        .not_valid_after(now + timedelta(days=30))
        .add_extension(x509.BasicConstraints(ca=ca, path_length=0 if ca else None), critical=True)
    )
    if ca:
        builder = builder.add_extension(x509.SubjectKeyIdentifier.from_public_key(public_key), critical=False)
    return builder.sign(issuer_key, hashes.SHA256())


def test_generated_crl_has_ca_authority_key_identifier_and_revoked_serial():
    module = _load_module()
    ca_key = ec.generate_private_key(ec.SECP384R1())
    ca_name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "Algo Test CA")])
    ca_cert = _certificate(ca_name, ca_name, ca_key.public_key(), ca_key, ca=True)

    client_key = ec.generate_private_key(ec.SECP384R1())
    client_name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "alice")])
    client_cert = _certificate(client_name, ca_name, client_key.public_key(), ca_key, ca=False)
    now = datetime.now(UTC).replace(microsecond=0)

    crl = module.build_crl(
        ca_certificate=ca_cert,
        ca_private_key=ca_key,
        last_update=now - timedelta(minutes=1),
        next_update=now + timedelta(days=30),
        revoked=[(client_cert.serial_number, now)],
    )

    ca_ski = ca_cert.extensions.get_extension_for_class(x509.SubjectKeyIdentifier).value.digest
    crl_aki = crl.extensions.get_extension_for_class(x509.AuthorityKeyIdentifier).value.key_identifier
    assert crl_aki == ca_ski
    assert [entry.serial_number for entry in crl] == [client_cert.serial_number]
    assert crl.is_signature_valid(ca_key.public_key())
    assert module.crl_matches(
        crl,
        ca_certificate=ca_cert,
        last_update=now - timedelta(minutes=1),
        next_update=now + timedelta(days=30),
        revoked=[(client_cert.serial_number, now)],
    )
    assert not module.crl_matches(
        crl,
        ca_certificate=ca_cert,
        last_update=now - timedelta(minutes=1),
        next_update=now + timedelta(days=30),
        revoked=[],
    )

    wrong_key = ec.generate_private_key(ec.SECP384R1())
    with pytest.raises(ValueError, match="does not match"):
        module.build_crl(
            ca_certificate=ca_cert,
            ca_private_key=wrong_key,
            last_update=now - timedelta(minutes=1),
            next_update=now + timedelta(days=30),
            revoked=[],
        )

    ski = ca_cert.extensions.get_extension_for_class(x509.SubjectKeyIdentifier).value
    sha384_crl = (
        x509.CertificateRevocationListBuilder()
        .issuer_name(ca_cert.subject)
        .last_update(now - timedelta(minutes=1))
        .next_update(now + timedelta(days=30))
        .add_extension(x509.AuthorityKeyIdentifier.from_issuer_subject_key_identifier(ski), critical=False)
        .add_revoked_certificate(
            x509.RevokedCertificateBuilder().serial_number(client_cert.serial_number).revocation_date(now).build()
        )
        .sign(ca_key, hashes.SHA384())
    )
    assert not module.crl_matches(
        sha384_crl,
        ca_certificate=ca_cert,
        last_update=now - timedelta(minutes=1),
        next_update=now + timedelta(days=30),
        revoked=[(client_cert.serial_number, now)],
    )
