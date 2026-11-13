"""Reject path traversal before destroy reads configuration or removes files."""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize(
    ("server", "valid", "region_setting"),
    [
        ("../victim", False, ""),
        ("..", False, ""),
        (".", False, ""),
        ("", False, ""),
        ("192.0.2.1", True, "algo_region:\n"),
        ("192.0.2.2", True, "algo_region: ''\n"),
        ("192.0.2.3", True, "algo_region: 3\n"),
        ("192.0.2.4", True, "algo_region: nyc3\n"),
        ("2001:db8::1", True, ""),
        ("vpn.example.com", True, ""),
    ],
)
def test_destroy_only_removes_one_server_directory(
    tmp_path: Path,
    server: str,
    valid: bool,
    region_setting: str,
):
    shutil.copy(ROOT / "destroy.yml", tmp_path)
    shutil.copy(ROOT / "config.cfg", tmp_path)
    (tmp_path / "playbooks").mkdir()
    shutil.copy(ROOT / "playbooks/rescue.yml", tmp_path / "playbooks")
    (tmp_path / "configs").mkdir()
    victim = tmp_path / "victim"
    victim.mkdir()
    (victim / ".config.yml").write_text(
        "algo_provider: local\nalgo_server_name: victim\n" + region_setting,
    )
    if valid:
        target = tmp_path / "configs" / server
        target.mkdir()
        shutil.copy(victim / ".config.yml", target)
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "ansible.cli.playbook",
            str(tmp_path / "destroy.yml"),
            "-i",
            "localhost,",
            "-c",
            "local",
            "-e",
            json.dumps(
                {
                    "server_ip": server,
                    "confirm_destroy": True,
                    "ansible_connection": "local",
                    "ansible_python_interpreter": sys.executable,
                }
            ),
        ],
        cwd=tmp_path,
        env={
            **os.environ,
            "ANSIBLE_LOCAL_TEMP": str(tmp_path / "ansible-tmp"),
            "ANSIBLE_REMOTE_TEMP": str(tmp_path / "module-tmp"),
        },
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    if valid:
        assert result.returncode == 0, result.stdout + result.stderr
        assert not (tmp_path / "configs" / server).exists()
    else:
        assert result.returncode != 0, result.stdout + result.stderr
        assert "single server directory" in result.stdout
    assert (victim / ".config.yml").exists()


def prepare_azure_destroy(tmp_path: Path) -> tuple[Path, Path]:
    """Copy production tasks and replace only package installation and Azure API operations."""
    for name in ("destroy.yml", "config.cfg"):
        shutil.copy(ROOT / name, tmp_path)
    (tmp_path / "playbooks").mkdir()
    shutil.copy(ROOT / "playbooks/rescue.yml", tmp_path / "playbooks")
    role = tmp_path / "roles/cloud-azure"
    shutil.copytree(ROOT / "roles/cloud-azure", role)
    server = tmp_path / "configs/192.0.2.1"
    server.mkdir(parents=True)
    (server / ".config.yml").write_text("algo_provider: azure\nalgo_server_name: test-vpn\n")
    binary = tmp_path / "uv"
    binary.write_text(
        f"#!{sys.executable}\nimport sys\nassert sys.argv[1:] == "
        "['sync', '--locked', '--inexact', '--extra', 'azure']\n"
    )
    binary.chmod(0o755)
    collection = tmp_path / "collections/ansible_collections/azure/azcollection/plugins/modules"
    collection.mkdir(parents=True)
    (collection / "azure_rm_resourcegroup.py").write_text(
        "from ansible.module_utils.basic import AnsibleModule\n"
        "import json, os\nfrom pathlib import Path\n"
        "module = AnsibleModule(argument_spec={\n"
        "    'name': {'type': 'str'}, 'state': {'type': 'str'},\n"
        "    'force_delete_nonempty': {'type': 'bool'},\n"
        "    'secret': {'type': 'str', 'no_log': True}, 'tenant': {'type': 'str'},\n"
        "    'client_id': {'type': 'str'}, 'subscription_id': {'type': 'str'},\n"
        "})\n"
        "Path(os.environ['DESTROY_TEST_CALL']).write_text(json.dumps(module.params))\n"
        "module.exit_json(changed=True)\n",
    )
    (collection / "azure_rm_resource_info.py").write_text(
        "from ansible.module_utils.basic import AnsibleModule\n"
        "module = AnsibleModule(argument_spec={})\n"
        "module.fail_json(msg='Unexpected region discovery during destruction')\n",
    )
    return server, tmp_path / "deleted.json"


def test_azure_destroy_does_not_require_region(tmp_path: Path):
    """Delete an old Azure deployment without prompting for or reading available regions."""
    server, call = prepare_azure_destroy(tmp_path)
    environment = {key: value for key, value in os.environ.items() if not key.startswith("AZURE_")}
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "ansible.cli.playbook",
            str(tmp_path / "destroy.yml"),
            "-i",
            "localhost,",
            "-c",
            "local",
            "-e",
            json.dumps(
                {
                    "server_ip": "192.0.2.1",
                    "confirm_destroy": True,
                    "azure_subscription_id": "test-subscription",
                    "ansible_python_interpreter": sys.executable,
                }
            ),
        ],
        cwd=tmp_path,
        env={
            **environment,
            "PATH": f"{tmp_path}:{os.environ['PATH']}",
            "ANSIBLE_COLLECTIONS_PATH": str(tmp_path / "collections"),
            "ANSIBLE_LOCAL_TEMP": str(tmp_path / "controller"),
            "ANSIBLE_REMOTE_TEMP": str(tmp_path / "remote"),
            "DESTROY_TEST_CALL": str(call),
        },
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert not server.exists()
    assert json.loads(call.read_text()) == {
        "name": "test-vpn",
        "state": "absent",
        "force_delete_nonempty": True,
        "subscription_id": "test-subscription",
        "secret": None,
        "tenant": None,
        "client_id": None,
    }
    assert "List regions" not in result.stdout
