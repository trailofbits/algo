"""Repository policy preventing generated credentials and VPN configs from becoming artifacts."""

import subprocess
from pathlib import Path

import yaml

ROOT = Path(__file__).parents[2]


def _tracked_paths():
    result = subprocess.run(["git", "ls-files", "-z"], cwd=ROOT, check=True, capture_output=True, text=True)
    return result.stdout.split("\0")


def test_generated_integration_credentials_are_never_tracked():
    forbidden_prefix = "tests/integration/test-configs/"
    forbidden_file = "tests/integration/test-run.log"
    offenders = [path for path in _tracked_paths() if path == forbidden_file or path.startswith(forbidden_prefix)]

    assert offenders == []


def test_no_generated_private_material_is_tracked_anywhere():
    forbidden_suffixes = {".key", ".p12", ".pfx", ".mobileconfig"}
    approved_fixture_prefix = "tests/fixtures/synthetic/"
    offenders = []
    private_key_markers = tuple(
        b"BEGIN " + key_type for key_type in (b"PRIVATE KEY", b"EC PRIVATE KEY", b"RSA PRIVATE KEY")
    )

    for tracked in _tracked_paths():
        if not tracked or tracked.startswith(approved_fixture_prefix):
            continue
        path = ROOT / tracked
        if not path.is_file():
            continue
        if path.suffix.lower() in forbidden_suffixes:
            offenders.append(tracked)
            continue
        try:
            content = path.read_bytes()
        except OSError:
            offenders.append(tracked)
            continue
        if any(marker in content for marker in private_key_markers):
            offenders.append(tracked)

    assert offenders == []


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
