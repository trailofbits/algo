"""Run Algo's OpenStack tasks against real collection and SDK resource shapes."""

import importlib
import io
import json
import os
from contextlib import redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from ansible.module_utils import basic
from ansible.parsing.dataloader import DataLoader
from ansible.template import Templar, trust_as_template

ROOT = Path(__file__).resolve().parents[1]

# SDK 4.22 calls its own deprecated hook when constructing every Resource.
# Keep all other SDK warnings visible; this hook is removed in SDK 5.
pytestmark = pytest.mark.filterwarnings(
    "ignore:The _compute_attributes method is deprecated for removal:Warning:openstack.resource"
)


@pytest.fixture
def cloud(monkeypatch):
    if os.environ.get("ALGO_CLOUD_SMOKE") == "1":
        sdk = importlib.import_module("openstack")
    else:
        sdk = pytest.importorskip("openstack", reason="Install the openstack extra")
    from openstack.compute.v2.flavor import Flavor
    from openstack.compute.v2.server import Server
    from openstack.connection import Connection
    from openstack.image.v2.image import Image
    from openstack.network.v2.network import Network
    from openstack.network.v2.security_group import SecurityGroup

    group = SecurityGroup(id="group-id", name="algo-security_group")
    network = Network(
        id="network-id",
        name="public",
        is_router_external=True,
        is_admin_state_up=True,
        status="ACTIVE",
    )
    flavors = [
        Flavor(id="large", ram=1024),
        Flavor(id="small", ram=512),
        Flavor(id="tiny", ram=256),
    ]
    server = Server(
        id="server-id",
        addresses={
            "public": [
                {"addr": "192.0.2.1", "version": 4, "OS-EXT-IPS:type": "fixed"},
                {"addr": "198.51.100.1", "version": 4, "OS-EXT-IPS:type": "floating"},
            ]
        },
    )
    image = Image(id="image-id", name="Ubuntu-22.04", status="active")
    connection = SimpleNamespace(
        network=Mock(),
        compute=Mock(),
        search_images=Mock(return_value=[image]),
        search_networks=Mock(return_value=[network]),
        range_search=lambda values, filters: Connection.range_search(None, values, filters),
        get_image_id=Mock(return_value="image-id"),
        create_server=Mock(return_value=server),
    )
    connection.network.find_security_group.return_value = None
    connection.network.create_security_group.return_value = group
    connection.compute.flavors.return_value = flavors
    connection.compute.find_flavor.return_value = flavors[1]
    connection.compute.find_server.return_value = None
    connection.compute.get_server.return_value = server
    monkeypatch.setattr(sdk, "connect", lambda **_kwargs: connection)
    return connection


def run_module(monkeypatch, action, arguments):
    """Execute collection logic and Ansible validation, replacing only SDK service calls."""
    module = importlib.import_module(
        f"ansible_collections.{action.rsplit('.', 1)[0]}.plugins.modules.{action.rsplit('.', 1)[1]}"
    )
    manifest = Path(module.__file__).parents[2] / "MANIFEST.json"
    assert json.loads(manifest.read_text())["collection_info"]["version"] == "2.6.0"
    module_args = json.dumps({"ANSIBLE_MODULE_ARGS": arguments}).encode()
    monkeypatch.setattr(basic, "_ANSIBLE_ARGS", module_args)
    monkeypatch.setattr(basic, "_ANSIBLE_PROFILE", "legacy")
    output = io.StringIO()
    with redirect_stdout(output), pytest.raises(SystemExit) as status:
        module.main()
    result = json.loads(output.getvalue())
    assert status.value.code == 0, result
    return result


@pytest.fixture
def deploy(monkeypatch, tmp_path, cloud):
    loader = DataLoader()
    loader.set_basedir(str(tmp_path))
    template = tmp_path / "files/cloud-init/base.yml"
    template.parent.mkdir(parents=True)
    template.write_text("#cloud-config\n")
    tasks = loader.load_from_file(
        str(ROOT / "roles/cloud-openstack/tasks/main.yml"),
        trusted_as_template=True,
    )

    def run():
        variables = {
            "algo_server_name": "algo",
            "ssh_port": 22,
            "wireguard_port": 51820,
            "wireguard_enabled": True,
            "ipsec_enabled": True,
            "cloud_providers": {"openstack": {"image": "Ubuntu-22.04", "flavor_ram": ">=512"}},
            "ansible_search_path": [str(tmp_path)],
        }
        for task in tasks:
            templar = Templar(loader=loader, variables=variables)
            if "set_fact" in task:
                variables.update(templar.template(task["set_fact"]))
            elif "assert" in task:
                for condition in task["assert"]["that"]:
                    expression = trust_as_template("{{ " + condition + " }}")
                    message = templar.template(task["assert"]["fail_msg"])
                    assert templar.template(expression), message
            else:
                apply_cloud_task(task, templar, variables, monkeypatch)
        return variables

    return run


def apply_cloud_task(task, templar, variables, monkeypatch):
    """Feed actual collection results into subsequent production task templates."""
    action = next((key for key in task if key.startswith("openstack.cloud.")), None)
    if action is None:
        return
    if "loop" in task:
        # Firewall protocol coverage lives in tests/network/test_cloud_firewalls.py.
        assert templar.template(task[action]["security_group"]) == "group-id"
        return
    arguments = templar.template(task[action]) if task[action] is not None else {}
    result = run_module(monkeypatch, action, arguments)
    variables[task["register"]] = result


def test_deployment_uses_current_collection_results(deploy, cloud):
    result = deploy()
    assert result["cloud_instance_ip"] == "198.51.100.1"
    assert result["flavor_id"] == "small"
    arguments = cloud.create_server.call_args.kwargs
    assert arguments["image"] == "image-id"
    assert arguments["flavor"] == "small"
    assert arguments["nics"] == [{"net-id": "network-id"}]
    assert arguments["security_groups"] == ["algo-security_group"]
    assert arguments["userdata"] == "#cloud-config\n"


def test_external_fixed_address_is_supported(deploy, cloud):
    server = cloud.compute.get_server.return_value
    server.addresses["public"] = server.addresses["public"][:1]
    assert deploy()["cloud_instance_ip"] == "192.0.2.1"


@pytest.mark.parametrize("missing", ["images", "flavors", "networks", "ipv4"])
def test_missing_resources_fail_clearly(deploy, cloud, missing):
    if missing == "images":
        cloud.search_images.return_value = []
    elif missing == "flavors":
        cloud.compute.flavors.return_value = []
    elif missing == "networks":
        cloud.search_networks.return_value = []
    else:
        cloud.compute.get_server.return_value.addresses = {
            "public": [{"version": 6, "addr": "2001:db8::1"}],
        }
    with pytest.raises(AssertionError, match="OpenStack"):
        deploy()
    if missing != "ipv4":
        cloud.network.create_security_group.assert_not_called()
        cloud.create_server.assert_not_called()


@pytest.mark.parametrize("resource", ["images", "networks"])
def test_ambiguous_resources_fail_clearly(deploy, cloud, resource):
    method = getattr(cloud, f"search_{resource}")
    method.return_value *= 2
    with pytest.raises(AssertionError, match="exactly one"):
        deploy()


def test_inactive_and_internal_networks_are_ignored(deploy, cloud):
    from openstack.network.v2.network import Network

    cloud.search_networks.return_value.extend(
        [
            Network(
                id="internal",
                is_router_external=False,
                is_admin_state_up=True,
                status="ACTIVE",
            ),
            Network(
                id="disabled",
                is_router_external=True,
                is_admin_state_up=False,
                status="ACTIVE",
            ),
            Network(id="down", is_router_external=True, is_admin_state_up=True, status="DOWN"),
        ]
    )
    assert deploy()["public_network_id"] == "network-id"


def test_sdk_authentication_error_is_reported(deploy, cloud):
    from openstack.exceptions import OpenStackCloudException

    cloud.search_images.side_effect = OpenStackCloudException("OpenStack authentication failed")
    with pytest.raises(AssertionError, match="authentication failed"):
        deploy()


@pytest.mark.parametrize(
    "auth_url, cloud_name, should_fail",
    [
        ("", "", True),
        ("https://identity.example", "", False),
        ("", "named-cloud", False),
    ],
)
def test_openrc_or_named_cloud(monkeypatch, auth_url, cloud_name, should_fail):
    monkeypatch.setenv("OS_AUTH_URL", auth_url)
    monkeypatch.setenv("OS_CLOUD", cloud_name)
    loader = DataLoader()
    tasks = loader.load_from_file(
        str(ROOT / "roles/cloud-openstack/tasks/main.yml"),
        trusted_as_template=True,
    )
    templar = Templar(loader=loader)
    expressions = (trust_as_template("{{ " + condition + " }}") for condition in tasks[0]["when"])
    assert all(templar.template(expression) for expression in expressions) == should_fail


def test_destroy_reports_api_failures(monkeypatch, cloud):
    from openstack.exceptions import OpenStackCloudException

    network = cloud.network
    network.find_security_group.return_value = network.create_security_group.return_value
    cloud.network.delete_security_group.side_effect = OpenStackCloudException("Deletion forbidden")
    loader = DataLoader()
    tasks = loader.load_from_file(
        str(ROOT / "roles/cloud-openstack/tasks/destroy.yml"),
        trusted_as_template=True,
    )
    task = tasks[1]
    templar = Templar(loader=loader, variables={"algo_server_name": "algo"})
    assert "failed_when" not in task and not task.get("ignore_errors")
    with pytest.raises(AssertionError, match="Deletion forbidden"):
        arguments = templar.template(task["openstack.cloud.security_group"])
        run_module(monkeypatch, "openstack.cloud.security_group", arguments)
