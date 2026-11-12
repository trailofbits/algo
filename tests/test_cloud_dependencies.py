"""Run real cloud-module checks with the same isolated startup as Ansible CLI."""

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


def require_extra(module: str) -> None:
    """Require optional SDKs in CI and allow base-only local test environments."""
    if importlib.util.find_spec(module) is not None:
        return
    if os.environ.get("ALGO_CLOUD_SMOKE") == "1":
        pytest.fail(f"Missing cloud dependency {module}; install the tested cloud extras")
    pytest.skip(f"Cloud dependency {module} is not installed")


def run_cloud_check(*arguments: str) -> None:
    """Start fresh collection discovery so template tests cannot change module resolution."""
    result = subprocess.run(
        [sys.executable, str(Path(__file__).with_name("cloud_module_smoke.py")), *arguments],
        capture_output=True,
        text=True,
        check=False,
        timeout=45,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_azure_modules_import():
    """Load actual deployment and teardown modules with their SDK operation groups."""
    require_extra("azure")
    run_cloud_check("azure")


def test_linode_modules_import():
    """Load actual stackscript and instance modules, including their specdoc imports."""
    require_extra("linode_api4")
    run_cloud_check("linode")


@pytest.mark.parametrize(
    "locations",
    [[{"name": "eastus", "metadata": {"regionType": "Physical"}}], []],
)
def test_azure_location_response(locations):
    """Run Azure's actual resource module with only its HTTP query replaced."""
    require_extra("azure")
    run_cloud_check("locations", json.dumps(locations))
