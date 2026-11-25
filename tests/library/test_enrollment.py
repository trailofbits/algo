"""Check state transitions for replacement devices, including pre-upgrade history."""

import json
import os
import subprocess
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
import yaml
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


@pytest.mark.parametrize(("entry", "index"), [("server.yml", 0), ("users.yml", 1)])
def test_enrollment_precedes_credentials_on_user_update(tmp_path, entry, index):
    root = Path(__file__).resolve().parents[2]
    tasks = yaml.safe_load((root / entry).read_text())[index]["tasks"][0]["block"]
    position, enroll = next((n, task) for n, task in enumerate(tasks) if "algo_enrollment" in task)
    assert all(n > position for n, task in enumerate(tasks) if "import_role" in task)
    playbook = tmp_path / "enroll.yml"
    playbook.write_text(yaml.safe_dump([{"hosts": "localhost", "gather_facts": False, "tasks": [enroll]}]))
    record = tmp_path / "configs/server/.users.json"
    args = [sys.executable, "-m", "ansible.cli.playbook", "-i", "localhost,", "-c", "local", str(playbook)]
    env = {**os.environ, "ANSIBLE_LOCAL_TEMP": str(tmp_path / "controller")}
    for tag in ("privacy", "update-users"):
        completed = subprocess.run(
            [*args, "--tags", tag, "-e", json.dumps({"IP_subject_alt_name": "server", "users": ["phone"]})],
            cwd=root,
            env=env,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        assert completed.returncode == 0, completed.stdout + completed.stderr
        assert record.exists() == (tag == "update-users")
    assert json.loads(record.read_text()) == {"active": ["phone"], "retired": []}
