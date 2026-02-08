"""Tests for scripts/list_servers.py."""

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

# Load list_servers module from scripts/ (not a Python package)
_script = Path(__file__).resolve().parents[2] / "scripts" / "list_servers.py"
_spec = importlib.util.spec_from_file_location("list_servers", str(_script))
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
list_servers = _mod.list_servers


@pytest.fixture()
def configs_dir(tmp_path):
    """Create a temporary configs directory with sample configs."""
    server1 = tmp_path / "10.0.0.1"
    server1.mkdir()
    (server1 / ".config.yml").write_text("server: 10.0.0.1\nalgo_provider: digitalocean\nalgo_server_name: algo\n")

    server2 = tmp_path / "10.0.0.2"
    server2.mkdir()
    (server2 / ".config.yml").write_text("server: 10.0.0.2\nalgo_provider: ec2\nalgo_server_name: prod\n")
    return tmp_path


def test_empty_directory(tmp_path):
    """Empty configs directory returns empty list."""
    assert list_servers(tmp_path) == []


def test_missing_directory(tmp_path):
    """Non-existent path returns empty list via glob."""
    assert list_servers(tmp_path / "nonexistent") == []


def test_lists_servers(configs_dir):
    """Parses .config.yml files and returns server metadata."""
    servers = list_servers(configs_dir)
    assert len(servers) == 2
    names = {s["algo_server_name"] for s in servers}
    assert names == {"algo", "prod"}


def test_sorted_output(configs_dir):
    """Servers are returned in sorted directory order."""
    servers = list_servers(configs_dir)
    ips = [s["server"] for s in servers]
    assert ips == ["10.0.0.1", "10.0.0.2"]


def test_skips_empty_yaml(tmp_path):
    """Empty YAML files (parsing to None) are skipped."""
    server = tmp_path / "10.0.0.5"
    server.mkdir()
    (server / ".config.yml").write_text("")

    assert list_servers(tmp_path) == []


def test_cli_output(tmp_path):
    """CLI outputs valid JSON to stdout."""
    server = tmp_path / "10.0.0.1"
    server.mkdir()
    (server / ".config.yml").write_text("server: 10.0.0.1\nalgo_server_name: test\n")

    result = subprocess.run(
        [sys.executable, "scripts/list_servers.py", str(tmp_path)],
        capture_output=True,
        text=True,
        check=True,
    )
    data = json.loads(result.stdout)
    assert len(data) == 1
    assert data[0]["server"] == "10.0.0.1"


def test_cli_missing_dir():
    """CLI outputs empty JSON array for missing directory."""
    result = subprocess.run(
        [
            sys.executable,
            "scripts/list_servers.py",
            "/nonexistent/path",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    assert json.loads(result.stdout) == []
