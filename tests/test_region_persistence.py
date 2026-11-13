"""Preserve the selected cloud region across provisioning and saved configuration."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize(
    ("selection", "expected"),
    [
        ({"region": "nyc3"}, "nyc3"),
        ({"_algo_region": {"user_input": "2"}}, "sfo3"),
        ({"_algo_region": {"user_input": ""}}, "nyc3"),
        pytest.param(None, "", id="provider-without-region"),
    ],
)
def test_region_survives_host_transition(
    tmp_path: Path,
    selection: dict | None,
    expected: str,
) -> None:
    """Run region selection, inventory creation, and config writing from production tasks."""
    prompts = yaml.safe_load((ROOT / "roles/cloud-digitalocean/tasks/prompts.yml").read_text())
    select = next(task for task in prompts if task.get("name") == "Set additional facts")
    cloud = yaml.safe_load((ROOT / "roles/cloud-digitalocean/tasks/main.yml").read_text())
    module = "digital_ocean_droplet"
    create = next(task[module] for task in cloud if module in task)
    check = {
        "assert": {"that": ["api_region == expected"]},
        "vars": {"api_region": create["region"], "expected": expected},
    }
    post = yaml.safe_load((ROOT / "playbooks/cloud-post.yml").read_text())
    inventory_name = "Add the server to an inventory group"
    inventory = next(task for task in post if task.get("name") == inventory_name)
    server = yaml.safe_load((ROOT / "server.yml").read_text())[0]["tasks"][0]["block"]
    final = next(task for task in server if task.get("tags") == "always")["block"]
    save = next(task for task in final if task.get("name") == "Dump the configuration")
    target = tmp_path / "configs/192.0.2.1"
    target.mkdir(parents=True)
    playbook = tmp_path / "region.yml"
    playbook.write_text(
        yaml.safe_dump(
            [
                {
                    "hosts": "localhost",
                    "gather_facts": False,
                    "tasks": ([select, check] if selection is not None else []) + [inventory],
                },
                {"hosts": "vpn-host", "gather_facts": False, "tasks": [save]},
            ]
        )
    )
    variables = {
        "cloud_instance_ip": "192.0.2.1",
        "algo_provider": "digitalocean",
        "algo_server_name": "region-test",
        "IP_subject_alt_name": "192.0.2.1",
        "algo_ondemand_cellular": False,
        "algo_ondemand_wifi": False,
        "algo_ondemand_wifi_exclude": "",
        "algo_dns_adblocking": False,
        "algo_ssh_tunneling": False,
        "algo_store_pki": True,
        "ipsec_enabled": True,
        "wireguard_enabled": True,
        "local_service_ip": "172.16.0.1",
        "local_service_ipv6": "fd00::1",
        "SSH_keys": {"private": "configs/algo.pem"},
        "do_regions": [{"slug": "nyc3"}, {"slug": "sfo3"}],
        "default_region": 1,
        "ansible_connection": "local",
        "ansible_python_interpreter": sys.executable,
        **(selection or {}),
    }
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
            json.dumps(variables),
        ],
        cwd=tmp_path,
        env={
            **os.environ,
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
    saved = yaml.safe_load((target / ".config.yml").read_text())
    assert saved["algo_region"] == expected
