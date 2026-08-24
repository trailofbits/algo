"""Behavioral tests for the interactive Algo launcher bootstrap."""

import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).parents[2]
LAUNCHER = ROOT / "algo"
LAUNCHER_PREFIX = LAUNCHER.read_text().split("# Check if uv is installed, if not, install it securely", 1)[0]


def test_wsl_powershell_receives_pinned_installer_values_as_arguments(tmp_path):
    stub_bin = tmp_path / "bin"
    stub_bin.mkdir()
    command_log = tmp_path / "powershell.log"
    powershell = stub_bin / "powershell.exe"
    powershell.write_text(
        """#!/bin/sh
printf '%s\n' "$*" > "$TEST_POWERSHELL_LOG"
"""
    )
    powershell.chmod(0o755)

    harness = tmp_path / "harness.sh"
    harness.write_text(f"{LAUNCHER_PREFIX}\ninstall_uv_via_download\n")
    harness.chmod(0o755)

    environment = os.environ.copy()
    environment.update(
        {
            "HOME": str(tmp_path / "home"),
            "OSTYPE": "linux-gnu",
            "PATH": f"{stub_bin}:/usr/bin:/bin",
            "TEST_POWERSHELL_LOG": str(command_log),
            "WSL_DISTRO_NAME": "Ubuntu",
        }
    )
    result = subprocess.run(
        ["/bin/bash", str(harness)],
        input="y\n",
        capture_output=True,
        text=True,
        env=environment,
    )

    assert result.returncode == 0, result.stderr
    invocation = command_log.read_text()
    assert "powershell.exe" not in invocation
    assert "https://github.com/astral-sh/uv/releases/download/0.12.3/uv-installer.ps1" in invocation
    assert "7b84813e3fad9586da122e362d4dcba1e2e611664244d004bcfc32b2fdf10430" in invocation
    assert "$env:UV_INSTALLER_URL" not in invocation
    assert "$env:UV_EXPECTED_SHA256" not in invocation


def test_checksum_command_failure_is_rejected_even_with_expected_output(tmp_path):
    stub_bin = tmp_path / "bin"
    stub_bin.mkdir()
    sha256sum = stub_bin / "sha256sum"
    sha256sum.write_text(
        """#!/bin/sh
printf '%s  %s\n' "$EXPECTED_SHA256" "$1"
exit 1
"""
    )
    sha256sum.chmod(0o755)
    payload = tmp_path / "installer.sh"
    payload.write_text(":\n")
    harness = tmp_path / "harness.sh"
    harness.write_text(
        f"""{LAUNCHER_PREFIX}
if ! verify_sha256 "$TEST_PAYLOAD" "$EXPECTED_SHA256"; then
  exit 1
fi
echo ACCEPTED
"""
    )
    harness.chmod(0o755)

    environment = os.environ.copy()
    environment.update(
        {
            "EXPECTED_SHA256": "a7e3924ea1cd06bf1518c577d635c624ae2e2db030e0fc8ff8cf426224384e17",
            "PATH": f"{stub_bin}:/usr/bin:/bin",
            "TEST_PAYLOAD": str(payload),
        }
    )
    result = subprocess.run(["/bin/bash", str(harness)], capture_output=True, text=True, env=environment)

    assert result.returncode != 0
    assert "ACCEPTED" not in result.stdout


def test_term_signal_cleans_up_and_stops_launcher(tmp_path):
    installer = tmp_path / "uv-installer.sh"
    installer.write_text(":\n")
    harness = tmp_path / "harness.sh"
    harness.write_text(
        f"""{LAUNCHER_PREFIX}
if ! declare -F handle_uv_installer_signal >/dev/null; then
  echo CONTINUED
  exit 0
fi
installer_path="$TEST_INSTALLER"
trap cleanup_uv_installer EXIT
trap handle_uv_installer_signal HUP INT TERM
kill -TERM $$
echo CONTINUED
"""
    )
    harness.chmod(0o755)

    environment = os.environ.copy()
    environment["TEST_INSTALLER"] = str(installer)
    result = subprocess.run(["/bin/bash", str(harness)], capture_output=True, text=True, env=environment)

    assert result.returncode != 0
    assert "CONTINUED" not in result.stdout
    assert not installer.exists()
