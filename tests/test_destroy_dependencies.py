"""Keep cloud teardown on the same locked dependencies used for deployment."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize(
    ("provider", "extra"),
    [("azure", "azure"), ("linode", "linode"), ("ec2", "aws"), ("scaleway", None), ("local", None)],
)
def test_destroy_installs_only_locked_provider_extras(tmp_path: Path, provider: str, extra: str | None):
    """Run the production install task with the uv process boundary recorded."""
    tasks = yaml.safe_load((ROOT / "destroy.yml").read_text())[0]["tasks"][0]["block"]
    install = next(task for task in tasks if task.get("name") == "Install cloud provider dependencies")
    recorded = tmp_path / "arguments.json"
    binary = tmp_path / "uv"
    binary.write_text(
        f"#!{sys.executable}\nimport json, sys\nfrom pathlib import Path\n"
        f"Path({str(recorded)!r}).write_text(json.dumps(sys.argv[1:]))\n",
    )
    binary.chmod(0o755)
    playbook = tmp_path / "dependencies.yml"
    playbook.write_text(
        yaml.safe_dump([{"hosts": "localhost", "gather_facts": False, "tasks": [install]}]),
    )
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "ansible.cli.playbook",
            str(playbook),
            "-i",
            "localhost,",
            "-c",
            "local",
            "-e",
            json.dumps({"algo_provider": provider, "ansible_python_interpreter": sys.executable}),
        ],
        cwd=ROOT,
        env={
            **os.environ,
            "PATH": f"{tmp_path}:{os.environ['PATH']}",
            "ANSIBLE_LOCAL_TEMP": str(tmp_path / "controller"),
            "ANSIBLE_REMOTE_TEMP": str(tmp_path / "remote"),
        },
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    if extra is None:
        assert not recorded.exists()
    else:
        assert json.loads(recorded.read_text()) == ["sync", "--locked", "--inexact", "--extra", extra]
