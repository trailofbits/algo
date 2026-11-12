"""Test command dispatch and dependency failures through the Bash launcher."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

LAUNCHER = Path(__file__).resolve().parents[1] / "algo"


@pytest.fixture
def launcher(tmp_path: Path):
    """Replace the external uv process with an argument recorder."""
    (tmp_path / "requirements.yml").write_text("collections: []\n")
    executable = tmp_path / "uv"
    executable.write_text(
        f"#!{sys.executable}\n"
        "import json, os, sys\n"
        "from pathlib import Path\n"
        "with Path('calls.jsonl').open('a') as stream:\n"
        "    stream.write(json.dumps(sys.argv[1:]) + '\\n')\n"
        "operation = 'COLLECTION' if 'ansible-galaxy' in sys.argv else 'COMMAND'\n"
        "sys.exit(int(os.environ.get(operation + '_STATUS', '0')))\n"
    )
    executable.chmod(0o700)
    return tmp_path


def run_launcher(directory: Path, args: list[str], **environment):
    return subprocess.run(
        ["/bin/bash", str(LAUNCHER), *args],
        cwd=directory,
        env={**os.environ, "PATH": str(directory), **environment},
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )


@pytest.mark.parametrize("option", ["help", "-h", "--help"])
def test_help_needs_no_dependencies(tmp_path: Path, option: str):
    result = run_launcher(tmp_path, [option])
    assert result.returncode == 0, result.stderr
    assert "Usage: ./algo" in result.stdout
    assert "Installing" not in result.stdout


def test_collection_failure_stops_deployment(launcher: Path):
    result = run_launcher(launcher, [], COLLECTION_STATUS="42")
    assert result.returncode != 0
    calls = [json.loads(line) for line in (launcher / "calls.jsonl").read_text().splitlines()]
    assert len(calls) == 1
    assert "ansible-galaxy" in calls[0]
    assert "collection" in result.stderr.lower()


@pytest.mark.parametrize(
    ("arguments", "playbook", "options"),
    [
        ([], "main.yml", []),
        (["-e", "name=two words"], "main.yml", ["-e", "name=two words"]),
        (["update-users"], "users.yml", ["-t", "update-users"]),
        (["destroy", "192.0.2.1"], "destroy.yml", ["-e", "server_ip=192.0.2.1"]),
    ],
)
def test_playbook_arguments_and_exit_status(launcher: Path, arguments, playbook, options):
    result = run_launcher(launcher, arguments, COMMAND_STATUS="23")
    assert result.returncode == 23
    calls = [json.loads(line) for line in (launcher / "calls.jsonl").read_text().splitlines()]
    assert calls[-1][-len(options) - 2 :] == ["ansible-playbook", playbook, *options]
