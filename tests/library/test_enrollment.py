"""Check state transitions for replacement devices, including pre-upgrade history."""

import json
from datetime import UTC, datetime, timedelta

import pytest
from algo_enrollment import reconcile
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.x509.oid import NameOID


def test_removed_devices_stay_retired(tmp_path):
    directory = tmp_path / "server"
    assert reconcile(directory, ["old", "phone"], check=True)
    assert not directory.exists()
    assert reconcile(directory, ["old", "phone"], check=False)
    assert reconcile(directory, ["phone"], check=False)
    with pytest.raises(ValueError, match="new device name"):
        reconcile(directory, ["OLD", "phone"], check=False)
    assert reconcile(directory, ["new", "phone"], check=True)
    assert json.loads((directory / ".users.json").read_text()) == {"active": ["phone"], "retired": ["old"]}
    assert reconcile(directory, ["new", "phone"], check=False)
    assert not reconcile(directory, ["phone", "new"], check=False)
    assert (directory / ".users.json").stat().st_mode & 0o777 == 0o600


def test_migrate_retired_certificate(tmp_path):
    directory = tmp_path / "server"
    pki = directory / "ipsec/.pki"
    (pki / "certs").mkdir(parents=True)
    (pki / "all-users").write_text("old\nphone\n")
    key = ec.generate_private_key(ec.SECP256R1())
    now = datetime.now(UTC)
    subject = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "old")])
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(subject)
        .public_key(key.public_key())
        .serial_number(55)
        .not_valid_before(now)
        .not_valid_after(now + timedelta(days=1))
        .sign(key, hashes.SHA256())
    )
    retired = x509.RevokedCertificateBuilder().serial_number(55).revocation_date(now).build()
    crl = (
        x509.CertificateRevocationListBuilder()
        .issuer_name(subject)
        .last_update(now)
        .next_update(now + timedelta(days=1))
        .add_revoked_certificate(retired)
        .sign(key, hashes.SHA256())
    )
    (pki / "crl.pem").write_bytes(crl.public_bytes(serialization.Encoding.PEM))
    with pytest.raises(ValueError, match="matching client certificates"):
        reconcile(directory, ["phone"], check=False)
    (pki / "certs/old.crt").write_bytes(cert.public_bytes(serialization.Encoding.PEM))
    with pytest.raises(ValueError, match="new device name"):
        reconcile(directory, ["old", "phone"], check=False)
    assert reconcile(directory, ["phone"], check=False)


def test_invalid_history_preserved(tmp_path):
    history = tmp_path / ".users.json"
    history.write_text('{"active":false}')
    with pytest.raises(ValueError, match="valid enrollment record"):
        reconcile(tmp_path, ["phone"], check=False)
    assert history.read_text() == '{"active":false}'
