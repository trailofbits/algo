"""Repository policy preventing generated credentials and VPN configs from becoming artifacts."""

import re
import subprocess
from pathlib import Path

import yaml

ROOT = Path(__file__).parents[2]
APPROVED_SYNTHETIC_CONTENT_FILES = {
    "docs/client-openwrt-router-wireguard.md",
    "tests/unit/test_config_validation.py",
    "tests/unit/test_docker_localhost_deployment.py",
    "tests/unit/test_generated_configs.py",
    "tests/unit/test_secret_artifact_policy.py",
    "tests/unit/test_wireguard_key_generation.py",
}


def _looks_like_private_material(tracked: str, content: bytes) -> bool:
    path = Path(tracked)
    if path.suffix.lower() in {".key", ".p12", ".pfx", ".mobileconfig", ".secrets"}:
        return True
    if path.name in {"id_rsa", "id_ecdsa", "id_ed25519", "id_dsa"}:
        return True
    if "/wireguard/.pki/private/" in f"/{tracked}":
        return True
    if tracked in APPROVED_SYNTHETIC_CONTENT_FILES:
        return False
    markers = (
        b"BEGIN PRIVATE KEY",
        b"BEGIN EC PRIVATE KEY",
        b"BEGIN RSA PRIVATE KEY",
        b"BEGIN OPENSSH PRIVATE KEY",
    )
    if any(marker in content for marker in markers):
        return True
    text = content.decode("utf-8", errors="ignore")
    return re.search(r"(?m)^\s*PrivateKey\s*=\s*(?!\{\{)\S+", text) is not None


def _tracked_paths():
    result = subprocess.run(["git", "ls-files", "-z"], cwd=ROOT, check=True, capture_output=True, text=True)
    return result.stdout.split("\0")


def test_generated_integration_credentials_are_never_tracked():
    forbidden_prefix = "tests/integration/test-configs/"
    forbidden_file = "tests/integration/test-run.log"
    offenders = [path for path in _tracked_paths() if path == forbidden_file or path.startswith(forbidden_prefix)]

    assert offenders == []


def test_no_generated_private_material_is_tracked_anywhere():
    approved_fixture_prefix = "tests/fixtures/synthetic/"
    offenders = []

    for tracked in _tracked_paths():
        if not tracked or tracked.startswith(approved_fixture_prefix):
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
        "configs/id_ed25519": b"synthetic-extensionless-key",
        "configs/vpn.secrets": b"client : EAP synthetic-password\n",
        "configs/key.txt": b"-----BEGIN OPENSSH PRIVATE KEY-----\nsynthetic\n",
        "scripts/leak.sh": b"-----BEGIN OPENSSH PRIVATE KEY-----\nreal-material\n",
    }
    assert all(_looks_like_private_material(path, content) for path, content in cases.items())


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
