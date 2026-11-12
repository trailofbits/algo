"""Exercise the provider installer without changing Python environments."""

import json
import os
import subprocess
import sys
from pathlib import Path

import yaml


def test_provider_install_uses_lock(tmp_path):
    """Install only supported extras, preserving the audited lock and other installed extras."""
    root = Path(__file__).resolve().parents[1]
    cloud_pre = yaml.safe_load((root / "playbooks/cloud-pre.yml").read_text())
    task_name = "Install cloud provider dependencies"
    task = next(task for task in cloud_pre[0]["block"] if task.get("name") == task_name)
    providers = [
        "ec2",
        "lightsail",
        "azure",
        "gce",
        "hetzner",
        "linode",
        "openstack",
        "cloudstack",
        "local",
        "digitalocean",
        "vultr",
        "scaleway",
    ]
    task["loop"] = providers
    task["vars"]["algo_provider"] = "{{ item }}"
    playbook = tmp_path / "install.yml"
    play = {"hosts": "localhost", "gather_facts": False, "tasks": [task]}
    playbook.write_text(yaml.safe_dump([play]))
    calls = tmp_path / "uv.jsonl"
    binary = tmp_path / "uv"
    binary.write_text(
        f"#!{sys.executable}\nimport json, sys\nfrom pathlib import Path\n"
        f"with Path({str(calls)!r}).open('a') as output:\n"
        "    output.write(json.dumps(sys.argv[1:]) + '\\n')\n",
    )
    binary.chmod(0o755)
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
            json.dumps({"ansible_python_interpreter": sys.executable}),
        ],
        cwd=root,
        env={
            **os.environ,
            "PATH": f"{tmp_path}:{os.environ['PATH']}",
            "ANSIBLE_LOCAL_TEMP": str(tmp_path / "controller"),
            "ANSIBLE_REMOTE_TEMP": str(tmp_path / "remote"),
        },
        capture_output=True,
        text=True,
        timeout=45,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert [json.loads(line) for line in calls.read_text().splitlines()] == [
        ["sync", "--locked", "--inexact", "--extra", extra]
        for extra in ["aws", "aws", "azure", "gcp", "hetzner", "linode", "openstack", "cloudstack"]
    ]
