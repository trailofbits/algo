"""Behavioral tests for the one-shot installer."""

import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).parents[2]
INSTALLER = ROOT / "install.sh"


def _write_stub(directory, name, body):
    path = directory / name
    path.write_text(f"#!/bin/sh\nset -eu\n{body}\n")
    path.chmod(0o755)


def _run_installer(tmp_path, *arguments, environment_overrides=None):
    stub_bin = tmp_path / "bin"
    stub_bin.mkdir()
    command_log = tmp_path / "commands.log"

    log_arguments = '''printf '%s' "$(basename "$0")" >> "$TEST_COMMAND_LOG"
for argument in "$@"; do
  printf '\t%s' "$argument" >> "$TEST_COMMAND_LOG"
done
printf '\n' >> "$TEST_COMMAND_LOG"'''

    _write_stub(stub_bin, "apt-get", log_arguments)
    _write_stub(stub_bin, "curl", f"{log_arguments}\nprintf ':\\n'")
    _write_stub(
        stub_bin,
        "git",
        log_arguments
        + """
if [ "${1:-}" = clone ]; then
  destination=''
  for argument in "$@"; do
    destination="$argument"
  done
  if [ "$destination" = /opt/algo ]; then
    destination="$TEST_ROOT/algo"
  fi
  mkdir -p "$destination"
fi""",
    )
    _write_stub(stub_bin, "uv", log_arguments)
    _write_stub(stub_bin, "jq", f"{log_arguments}\nprintf '[\"user1\"]\\n'")
    _write_stub(stub_bin, "tee", f"{log_arguments}\n/bin/cat >/dev/null")

    harness = tmp_path / "harness.sh"
    harness.write_text(
        """#!/bin/sh
set -eu
cd() {
  case "${1:-}" in
    /opt | /opt/)
      command cd "$TEST_ROOT"
      ;;
    /opt/algo)
      command cd "$TEST_ROOT/algo"
      ;;
    *)
      command cd "$@"
      ;;
  esac
}
. "$INSTALLER" "$@"
"""
    )
    harness.chmod(0o755)

    environment = os.environ.copy()
    environment.update(
        {
            "ANSIBLE_EXTRA_ARGS": "",
            "HOME": str(tmp_path / "home"),
            "INSTALLER": str(INSTALLER),
            "METHOD": "local",
            "PATH": f"{stub_bin}:/usr/bin:/bin",
            "TEST_COMMAND_LOG": str(command_log),
            "TEST_ROOT": str(tmp_path),
        }
    )
    environment.update(environment_overrides or {})
    result = subprocess.run(
        ["/bin/sh", str(harness), *arguments],
        capture_output=True,
        text=True,
        env=environment,
    )
    commands = [line.split("\t") for line in command_log.read_text().splitlines()] if command_log.exists() else []
    return result, commands


def test_installer_clones_main_after_installing_prerequisites(tmp_path):
    result, commands = _run_installer(tmp_path)

    assert result.returncode == 0, result.stderr
    assert ["apt-get", "install", "-y", "curl", "git", "jq"] in commands
    assert [
        "git",
        "clone",
        "--branch",
        "main",
        "https://github.com/trailofbits/algo.git",
        "/opt/algo",
    ] in commands


def test_installer_rejects_positional_arguments_before_side_effects(tmp_path):
    result, commands = _run_installer(tmp_path, "local")

    assert result.returncode == 2
    assert "positional arguments are not supported" in result.stderr
    assert commands == []


def test_installer_rejects_invalid_method_before_side_effects(tmp_path):
    result, commands = _run_installer(tmp_path, environment_overrides={"METHOD": "invalid"})

    assert result.returncode == 2
    assert "METHOD must be 'cloud' or 'local'" in result.stderr
    assert commands == []
