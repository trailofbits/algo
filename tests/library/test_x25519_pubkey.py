"""Exercise the Ansible module's public JSON interface and key-file formats."""

import base64
import json
import shutil
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey
from hypothesis import example, given, settings
from hypothesis import strategies as st

MODULE = Path(__file__).resolve().parents[2] / "library" / "x25519_pubkey.py"
PRIVATE_KEY = base64.b64encode(bytes(range(32))).decode()


def run_module(**params):
    """Run the real module, including Ansible's argument validation."""
    process = subprocess.run(
        [sys.executable, str(MODULE)],
        input=json.dumps({"ANSIBLE_MODULE_ARGS": params}),
        text=True,
        capture_output=True,
        timeout=10,
        check=False,
    )
    result = json.loads(process.stdout)
    assert bool(process.returncode) == result.get("failed", False), process.stderr
    return result


@settings(max_examples=20, deadline=None)
@example(key=b"A" * 32)
@example(key=b"\t" + b"\0" * 30 + b"\n")
@given(key=st.binary(min_size=32, max_size=32))
def test_raw_and_base64_files_derive_the_same_public_key(key: bytes):
    """Every 32-byte value is a valid raw key, even when it resembles base64."""
    public_key = X25519PrivateKey.from_private_bytes(key).public_key().public_bytes_raw()
    expected = base64.b64encode(public_key).decode()
    with TemporaryDirectory() as directory:
        path = Path(directory) / "private.key"
        for contents in (key, b"\n" + base64.b64encode(key) + b"\n"):
            path.write_bytes(contents)
            result = run_module(private_key_path=str(path))
            assert not result.get("failed"), result
            assert result["public_key"] == expected
            assert result["changed"] is False


def test_output_is_idempotent_and_private_argument_is_redacted(tmp_path: Path):
    path = tmp_path / "public.key"
    first = run_module(private_key_b64=PRIVATE_KEY, public_key_path=str(path))
    assert first["changed"] is True
    assert path.read_text() == first["public_key"]
    assert PRIVATE_KEY not in json.dumps(first)
    second = run_module(private_key_b64=PRIVATE_KEY, public_key_path=str(path))
    assert second["changed"] is False
    assert second["public_key"] == first["public_key"]


@pytest.mark.parametrize("existing", [None, "old key", "unchanged"])
def test_check_mode_reports_changes_without_writing(tmp_path: Path, existing: str | None):
    path = tmp_path / "public.key"
    expected = run_module(private_key_b64=PRIVATE_KEY)["public_key"]
    contents = expected if existing == "unchanged" else existing
    if contents is not None:
        path.write_text(contents)
    result = run_module(
        private_key_b64=PRIVATE_KEY,
        public_key_path=str(path),
        _ansible_check_mode=True,
    )
    assert result["changed"] is (contents != expected)
    assert result["public_key"] == expected
    assert (path.read_text() if path.exists() else None) == contents


@pytest.mark.parametrize("key", ["", "!", "é", base64.b64encode(b"short").decode()])
def test_invalid_base64_argument_fails(key: str):
    result = run_module(private_key_b64=key)
    assert result["failed"] is True
    assert "private key" in result["msg"].lower()


@pytest.mark.parametrize("contents", [b"", b"!", base64.b64encode(b"short")])
def test_invalid_private_key_file_fails(tmp_path: Path, contents: bytes):
    path = tmp_path / "private.key"
    path.write_bytes(contents)
    result = run_module(private_key_path=str(path))
    assert result["failed"] is True
    assert "private key" in result["msg"].lower()


def test_missing_private_key_fails():
    assert run_module()["failed"] is True


def test_unreadable_private_key_fails(tmp_path: Path):
    path = tmp_path / "missing.key"
    result = run_module(private_key_path=str(path))
    assert result["failed"] is True
    assert "read private key" in result["msg"]
    assert str(path) in result["msg"]


def test_unwritable_public_key_fails(tmp_path: Path):
    path = tmp_path / "missing" / "public.key"
    result = run_module(private_key_b64=PRIVATE_KEY, public_key_path=str(path))
    assert result["failed"] is True
    assert "write public key" in result["msg"]
    assert str(path) in result["msg"]


def test_unreadable_existing_public_key_fails(tmp_path: Path):
    result = run_module(private_key_b64=PRIVATE_KEY, public_key_path=str(tmp_path))
    assert result["failed"] is True
    assert "read public key" in result["msg"]


def test_invalid_text_in_existing_public_key_fails(tmp_path: Path):
    path = tmp_path / "public.key"
    path.write_bytes(b"\xff")
    result = run_module(private_key_b64=PRIVATE_KEY, public_key_path=str(path))
    assert result["failed"] is True
    assert "read public key" in result["msg"]
    assert path.read_bytes() == b"\xff"


def test_key_matches_wireguard():
    if not shutil.which("wg"):
        pytest.skip("WireGuard tools are not installed")
    process = subprocess.run(
        ["wg", "pubkey"],
        input=PRIVATE_KEY,
        text=True,
        capture_output=True,
        timeout=10,
        check=True,
    )
    assert run_module(private_key_b64=PRIVATE_KEY)["public_key"] == process.stdout.strip()
