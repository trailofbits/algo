"""Exercise GCE teardown through the playbook with cloud requests recorded locally."""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
ADDRESS = "198.51.100.10"

# Only the cloud API and dependency installation are replaced. The production
# playbooks load credentials, resolve the region, select resources, and clean up.
API_STUB = """
from pathlib import Path
from ansible.module_utils.basic import AnsibleModule
import json, os
module = AnsibleModule(argument_spec=dict(
    auth_kind=dict(), service_account_file=dict(), project=dict(), region=dict(),
    scope=dict(), zone=dict(), filters=dict(type='list', elements='str'), state=dict(), name=dict(),
))
params = module.params
with Path(os.environ['CLOUD_CALLS']).open('a') as calls:
    calls.write(json.dumps([ACTION, params]) + '\\n')
if ACTION in ('gcp_compute_firewall_info', 'gcp_compute_network_info'):
    ident = '4' if ACTION == 'gcp_compute_network_info' else '3'
    if os.environ['SCENARIO'] == 'replaced-network' and ident == '4':
        ident = '44'
    module.exit_json(resources=[] if os.environ['SCENARIO'] == 'gone' else [{'id': ident}])
if ACTION == 'gcp_compute_instance_info':
    instances = json.loads(os.environ['INSTANCES'])
    module.exit_json(resources=[instance for instance in instances if instance['zone'].endswith('/' + params['zone'])])
if ACTION == 'gcp_compute_address_info':
    module.exit_json(resources=json.loads(os.environ['ADDRESSES']))
if ACTION == 'gcp_compute_address' and os.environ['FAIL_RELEASE'] == '1':
    module.fail_json(msg='address still in use')
module.exit_json(changed=True)
"""


@pytest.mark.parametrize(
    "scenario",
    [
        "found",
        "gone",
        "wrong-project",
        "wrong-zone",
        "replaced-instance",
        "replaced-network",
        "legacy",
        "legacy-unconfirmed",
        "legacy-different-ip",
        "legacy-gone",
        "release-failed",
    ],
)
def test_destroy_deletes_only_owned_resources(tmp_path, scenario):
    for name in ["config.cfg", "destroy.yml"]:
        shutil.copy(ROOT / name, tmp_path)
    shutil.copytree(ROOT / "playbooks", tmp_path / "playbooks")
    shutil.copytree(ROOT / "roles/cloud-gce", tmp_path / "roles/cloud-gce")
    config = tmp_path / "configs" / ADDRESS
    config.mkdir(parents=True)
    (config / ".config.yml").write_text(
        f"algo_provider: gce\nalgo_region: test-r\nalgo_server_name: vpn\nserver: {ADDRESS}\n"
    )
    extra = {"server_ip": ADDRESS, "confirm_destroy": True, "ansible_python_interpreter": sys.executable}
    if scenario.startswith("legacy"):
        if scenario != "legacy-unconfirmed":
            extra.update(gce_legacy_project="test-project", gce_legacy_zone="test-r-b")
    else:
        with (config / ".config.yml").open("a") as saved:
            saved.write(
                yaml.safe_dump(
                    {
                        "gce_deployment": {
                            "project": "unrelated" if scenario == "wrong-project" else "test-project",
                            "zone": "another-r-b" if scenario == "wrong-zone" else "test-r-b",
                            "region": "test-r",
                            "instance_id": "1",
                            "address_id": "2",
                            "firewall_id": "3",
                            "network_id": "4",
                            "network_name": "algo-123",
                        }
                    }
                )
            )
    credentials = tmp_path / "credentials.json"
    credentials.write_text('{"project_id":"test-project"}')
    uv = tmp_path / "uv"
    uv.write_text("#!/bin/sh\nexit 0\n")
    uv.chmod(0o755)
    library = tmp_path / "library"
    library.mkdir()
    for name in [
        "instance_info",
        "address_info",
        "firewall_info",
        "network_info",
        "instance",
        "address",
        "firewall",
        "network",
    ]:
        module = f"gcp_compute_{name}"
        (library / f"{module}.py").write_text(f"#!/usr/bin/python\nACTION={module!r}\n" + API_STUB)
    instances = [
        {
            "id": "99" if scenario == "replaced-instance" else "1",
            "zone": "zones/test-r-b",
            "networkInterfaces": [
                {"accessConfigs": [{"natIP": "198.51.100.11" if scenario == "legacy-different-ip" else ADDRESS}]}
            ],
        }
    ]
    calls_file = tmp_path / "calls"
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "ansible.cli.playbook",
            "destroy.yml",
            "-i",
            "localhost,",
            "-c",
            "local",
            "-e",
            json.dumps(extra),
        ],
        cwd=tmp_path,
        env={
            **os.environ,
            "PATH": f"{tmp_path}:{os.environ['PATH']}",
            "GCE_CREDENTIALS_FILE_PATH": str(credentials),
            "CLOUD_CALLS": str(calls_file),
            "SCENARIO": scenario,
            "INSTANCES": json.dumps([] if scenario in {"gone", "legacy-gone"} else instances),
            "ADDRESSES": json.dumps([] if scenario in {"gone", "legacy-gone"} else [{"id": "2", "address": ADDRESS}]),
            "FAIL_RELEASE": str(int(scenario == "release-failed")),
            "ANSIBLE_LIBRARY": str(library),
            "ANSIBLE_LOCAL_TEMP": str(tmp_path / "controller"),
            "ANSIBLE_REMOTE_TEMP": str(tmp_path / "remote"),
        },
        capture_output=True,
        text=True,
        timeout=45,
        check=False,
    )
    success = scenario in {"gone", "found", "legacy"}
    assert (proc.returncode == 0) == success, proc.stdout + proc.stderr
    assert config.exists() != success
    calls = [json.loads(line) for line in calls_file.read_text().splitlines()] if calls_file.exists() else []
    writes = [(action, args) for action, args in calls if args["state"] == "absent"]
    if scenario in {"found", "legacy", "release-failed"}:
        expected = ["gcp_compute_instance", "gcp_compute_address"]
        if scenario == "found":
            expected.extend(["gcp_compute_firewall", "gcp_compute_network"])
            assert all(params["name"] == "algo-123" for _, params in writes[1:])
        assert [action for action, _ in writes] == expected
        assert writes[0][1]["zone"] == "test-r-b"
        assert writes[1][1]["region"] == "test-r"
    else:
        assert writes == []
