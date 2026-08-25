"""Repository policy preventing generated credentials and VPN configs from becoming artifacts."""

import re
import subprocess
from pathlib import Path

import yaml
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec

ROOT = Path(__file__).parents[2]
APPROVED_SYNTHETIC_VALUES = {
    "docs/client-openwrt-router-wireguard.md": (b"<your_private_key>", b"<preshared_key>"),
    "tests/unit/test_config_validation.py": (b"aGVsbG8gd29ybGQgdGhpcyBpcyBub3QgYSByZWFsIGtleQo=",),
    "tests/unit/test_docker_localhost_deployment.py": (b"EEHcgpEB8JIlUZpYnt3PqJJgfwgRGDQNlGH7gYkMVGo=",),
    "tests/unit/test_generated_configs.py": (b"SAMPLE_PRIVATE_KEY_BASE64==", b"SAMPLE_PRESHARED_KEY_BASE64=="),
    "tests/unit/test_wireguard_key_generation.py": (b"{b64_key}",),
}


def _der_sequences(content: bytes):
    """Yield bounded DER SEQUENCE objects, including objects embedded in larger files."""
    for start, tag in enumerate(content):
        if tag != 0x30 or start + 2 > len(content):
            continue
        first_length = content[start + 1]
        if first_length < 0x80:
            header_length = 2
            value_length = first_length
        else:
            length_octets = first_length & 0x7F
            if length_octets == 0 or length_octets > 4 or start + 2 + length_octets > len(content):
                continue
            header_length = 2 + length_octets
            value_length = int.from_bytes(content[start + 2 : start + header_length], "big")
        end = start + header_length + value_length
        if end <= len(content):
            yield content[start:end]


def _looks_like_private_material(tracked: str, content: bytes) -> bool:
    path = Path(tracked)
    if path.suffix.lower() in {".key", ".p12", ".pfx", ".mobileconfig", ".secrets"}:
        return True
    if path.name in {"id_rsa", "id_ecdsa", "id_ed25519", "id_dsa"}:
        return True
    if "/wireguard/.pki/private/" in f"/{tracked}":
        return True
    for value in APPROVED_SYNTHETIC_VALUES.get(tracked, ()):
        content = content.replace(value, b"<approved-synthetic-value>")
    markers = (
        b"BEGIN " + kind + b"PRIVATE KEY" for kind in (b"", b"EC ", b"RSA ", b"OPENSSH ", b"ENCRYPTED ", b"DSA ")
    )
    if any(marker in content for marker in markers):
        return True
    for candidate in _der_sequences(content):
        for password in (None, b"algo-private-key-detector"):
            try:
                serialization.load_der_private_key(candidate, password=password)
                return True
            except TypeError as error:
                if "private key is encrypted" in str(error) or "private key is not encrypted" in str(error):
                    return True
            except ValueError:
                pass
    text = content.decode("utf-8", errors="ignore")
    return (
        re.search(
            r"(?m)^\s*(?:PrivateKey|PresharedKey)\s*=\s*(?!\{\{)(?!<approved-synthetic-value>)\S+",
            text,
        )
        is not None
    )


def _tracked_paths():
    result = subprocess.run(["git", "ls-files", "-z"], cwd=ROOT, check=True, capture_output=True, text=True)
    return result.stdout.split("\0")


def test_generated_integration_credentials_are_never_tracked():
    forbidden_prefix = "tests/integration/test-configs/"
    forbidden_file = "tests/integration/test-run.log"
    offenders = [path for path in _tracked_paths() if path == forbidden_file or path.startswith(forbidden_prefix)]

    assert offenders == []


def test_no_generated_private_material_is_tracked_anywhere():
    offenders = []

    for tracked in _tracked_paths():
        if not tracked:
            continue
        path = ROOT / tracked
        if not path.is_file():
            continue
        try:
            content = path.read_bytes()
        except OSError:
            offenders.append(tracked)
            continue
        if _looks_like_private_material(tracked, content):
            offenders.append(tracked)

    assert offenders == []


def test_private_material_detector_covers_wireguard_openssh_and_secret_files():
    cases = {
        "configs/client.conf": b"[Interface]\nPrivateKey = synthetic-value\n",
        "configs/peer.conf": b"[Peer]\nPresharedKey = synthetic-value\n",
        "configs/id_ed25519": b"synthetic-extensionless-key",
        "configs/vpn.secrets": b"client : EAP synthetic-password\n",
        "configs/key.txt": b"-----BEGIN " + b"OPENSSH PRIVATE KEY-----\nsynthetic\n",
        "configs/encrypted.pem": b"-----BEGIN " + b"ENCRYPTED PRIVATE KEY-----\nsynthetic\n",
        "configs/dsa.pem": b"-----BEGIN " + b"DSA PRIVATE KEY-----\nsynthetic\n",
        "scripts/leak.sh": b"-----BEGIN " + b"OPENSSH PRIVATE KEY-----\nreal-material\n",
        "tests/fixtures/synthetic/leak.conf": b"[Interface]\nPrivateKey = real-material\n",
    }
    assert all(_looks_like_private_material(path, content) for path, content in cases.items())


def test_approved_synthetic_files_do_not_hide_new_private_material():
    for path in APPROVED_SYNTHETIC_VALUES:
        material = b"-----BEGIN " + b"OPENSSH PRIVATE KEY-----\nnew-material\n"
        assert _looks_like_private_material(path, material)


def test_binary_der_private_key_is_detected_without_a_secret_extension():
    private_key = ec.generate_private_key(ec.SECP256R1())
    unencrypted = private_key.private_bytes(
        serialization.Encoding.DER,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    )
    encrypted = private_key.private_bytes(
        serialization.Encoding.DER,
        serialization.PrivateFormat.PKCS8,
        serialization.BestAvailableEncryption(b"test-password"),
    )

    for material in (unencrypted, encrypted):
        assert _looks_like_private_material("artifacts/opaque.bin", material)
        assert _looks_like_private_material("artifacts/embedded.bin", b"benign-prefix" + material + b"benign-suffix")
        for path, values in APPROVED_SYNTHETIC_VALUES.items():
            assert _looks_like_private_material(path, values[0] + b"\n" + material + b"\n")


def test_noninteractive_or_test_mode_never_prints_generated_completion_credentials():
    server = (ROOT / "server.yml").read_text(encoding="utf-8")
    completion = server.rsplit("- debug:", 1)[1].split("rescue:", 1)[0]

    assert 'no_log: "{{ (tests | default(false) | bool) or (algo_no_log | default(false) | bool) }}"' in completion


def test_generated_integration_credentials_are_ignored():
    patterns = (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
    assert "/tests/integration/test-configs/" in patterns
    assert "/tests/integration/test-run.log" in patterns


def test_integration_configs_are_ephemeral_and_never_uploaded_or_logged():
    path = ROOT / ".github" / "workflows" / "integration-tests.yml"
    text = path.read_text(encoding="utf-8")
    workflow = yaml.safe_load(text)
    steps = workflow["jobs"]["localhost-deployment"]["steps"]
    commands = "\n".join(step.get("run", "") for step in steps)
    artifact_paths = [
        step.get("with", {}).get("path") for step in steps if "actions/upload-artifact@" in step.get("uses", "")
    ]

    assert "${RUNNER_TEMP}/algo-configs" in commands
    assert "ln -s" in commands
    assert "no_log: true" in text
    assert "path: configs/" not in text
    assert "cat configs/" not in commands
    assert "Server public key:" not in commands
    assert artifact_paths == ["${{ runner.temp }}/algo-diagnostics.txt"]

    diagnostic_step = next(step for step in steps if step.get("name") == "Create sanitized diagnostics on failure")
    diagnostic_command = diagnostic_step["run"].casefold()
    for forbidden in ("configs/", "private", "password", "secret", "token", ".pem", ".p12", ".key"):
        assert forbidden not in diagnostic_command
    assert "vpn_type=" in diagnostic_command
    assert "wireguard_service=" in diagnostic_command
    assert "strongswan_service=" in diagnostic_command
    assert "dnsmasq_service=" in diagnostic_command
