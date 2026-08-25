"""CRL generation contract required by StrongSwan strict revocation."""

import importlib.util
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.x509.oid import ExtensionOID, NameOID

ROOT = Path(__file__).parents[2]
MODULE_PATH = ROOT / "library/x509_crl_aki.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("x509_crl_aki", MODULE_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _certificate(subject: x509.Name, issuer: x509.Name, public_key, issuer_key, *, ca: bool, include_ski: bool = True):
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
    if ca and include_ski:
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


def test_generated_crl_for_ski_less_ca_is_idempotent():
    module = _load_module()
    ca_key = ec.generate_private_key(ec.SECP384R1())
    ca_name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "SKI-less Algo Test CA")])
    ca_cert = _certificate(ca_name, ca_name, ca_key.public_key(), ca_key, ca=True, include_ski=False)
    now = datetime.now(UTC).replace(microsecond=0)
    last_update = now - timedelta(minutes=1)
    next_update = now + timedelta(days=30)

    crl = module.build_crl(
        ca_certificate=ca_cert,
        ca_private_key=ca_key,
        last_update=last_update,
        next_update=next_update,
        revoked=[],
    )

    assert module.crl_matches(
        crl,
        ca_certificate=ca_cert,
        last_update=last_update,
        next_update=next_update,
        revoked=[],
    )


def test_crl_match_rejects_noncanonical_extension_profile():
    module = _load_module()
    ca_key = ec.generate_private_key(ec.SECP384R1())
    ca_name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "Algo Test CA")])
    ca_cert = _certificate(ca_name, ca_name, ca_key.public_key(), ca_key, ca=True)
    now = datetime.now(UTC).replace(microsecond=0)
    last_update = now - timedelta(minutes=1)
    next_update = now + timedelta(days=30)
    ski = ca_cert.extensions.get_extension_for_class(x509.SubjectKeyIdentifier).value
    malformed = (
        x509.CertificateRevocationListBuilder()
        .issuer_name(ca_cert.subject)
        .last_update(last_update)
        .next_update(next_update)
        .add_extension(x509.AuthorityKeyIdentifier.from_issuer_subject_key_identifier(ski), critical=True)
        .add_extension(x509.CRLNumber(1), critical=False)
        .sign(ca_key, hashes.SHA256())
    )

    assert not module.crl_matches(
        malformed,
        ca_certificate=ca_cert,
        last_update=last_update,
        next_update=next_update,
        revoked=[],
    )

    expected_aki = x509.AuthorityKeyIdentifier.from_issuer_subject_key_identifier(ski)
    conflicting_aki = x509.AuthorityKeyIdentifier(
        key_identifier=expected_aki.key_identifier,
        authority_cert_issuer=[x509.DirectoryName(ca_cert.issuer)],
        authority_cert_serial_number=ca_cert.serial_number,
    )
    revoked_at = now
    restricted_entry = (
        x509.RevokedCertificateBuilder()
        .serial_number(7)
        .revocation_date(revoked_at)
        .add_extension(x509.CRLReason(x509.ReasonFlags.key_compromise), critical=False)
        .build()
    )
    malformed_entry = (
        x509.CertificateRevocationListBuilder()
        .issuer_name(ca_cert.subject)
        .last_update(last_update)
        .next_update(next_update)
        .add_extension(conflicting_aki, critical=False)
        .add_revoked_certificate(restricted_entry)
        .sign(ca_key, hashes.SHA256())
    )
    assert not module.crl_matches(
        malformed_entry,
        ca_certificate=ca_cert,
        last_update=last_update,
        next_update=next_update,
        revoked=[(7, revoked_at)],
    )


def test_key_binding_is_validated_even_when_existing_crl_matches():
    module = _load_module()
    ca_key = ec.generate_private_key(ec.SECP384R1())
    wrong_key = ec.generate_private_key(ec.SECP384R1())
    ca_name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "Algo Test CA")])
    ca_cert = _certificate(ca_name, ca_name, ca_key.public_key(), ca_key, ca=True)

    with pytest.raises(ValueError, match="does not match"):
        module.validate_ca_private_key(ca_cert, wrong_key)


def test_duplicate_crl_extensions_are_noncanonical_not_fatal():
    module = _load_module()
    ca_key = ec.generate_private_key(ec.SECP384R1())
    ca_name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "Algo Test CA")])
    ca_cert = _certificate(ca_name, ca_name, ca_key.public_key(), ca_key, ca=True)
    now = datetime.now(UTC).replace(microsecond=0)

    class DuplicateExtensionCRL:
        @property
        def extensions(self):
            raise x509.DuplicateExtension("duplicate AKI", ExtensionOID.AUTHORITY_KEY_IDENTIFIER)

    assert not module.crl_matches(
        DuplicateExtensionCRL(),
        ca_certificate=ca_cert,
        last_update=now,
        next_update=now + timedelta(days=30),
        revoked=[],
    )


@pytest.mark.parametrize("check_mode", [False, True])
def test_module_reports_mode_only_correction_as_changed(tmp_path, monkeypatch, check_mode):
    module = _load_module()
    ca_key = ec.generate_private_key(ec.SECP384R1())
    ca_name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "Algo Test CA")])
    ca_cert = _certificate(ca_name, ca_name, ca_key.public_key(), ca_key, ca=True)
    now = datetime.now(UTC).replace(microsecond=0)
    last_update = now - timedelta(minutes=1)
    next_update = now + timedelta(days=30)

    ca_path = tmp_path / "ca.crt"
    key_path = tmp_path / "ca.key"
    crl_path = tmp_path / "crl.pem"
    ca_path.write_bytes(ca_cert.public_bytes(serialization.Encoding.PEM))
    key_path.write_bytes(
        ca_key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.BestAvailableEncryption(b"test-passphrase"),
        )
    )
    crl_path.write_bytes(
        module.build_crl(
            ca_certificate=ca_cert,
            ca_private_key=ca_key,
            last_update=last_update,
            next_update=next_update,
            revoked=[],
        ).public_bytes(serialization.Encoding.PEM)
    )
    crl_path.chmod(0o600)

    class FakeAnsibleModule:
        def __init__(self):
            self.params = {
                "path": str(crl_path),
                "ca_certificate_path": str(ca_path),
                "privatekey_path": str(key_path),
                "privatekey_passphrase": "test-passphrase",
                "last_update": last_update.strftime("%Y%m%d%H%M%SZ"),
                "next_update": next_update.strftime("%Y%m%d%H%M%SZ"),
                "revoked_certificates": [],
                "mode": "0644",
            }
            self.check_mode = check_mode
            self.result = None

        def exit_json(self, **result):
            self.result = result

        def fail_json(self, **result):
            pytest.fail(result["msg"])

    fake = FakeAnsibleModule()
    monkeypatch.setattr(module, "AnsibleModule", lambda **_kwargs: fake)

    module.main()

    assert fake.result["changed"] is True
    assert (crl_path.stat().st_mode & 0o777) == (0o600 if check_mode else 0o644)
