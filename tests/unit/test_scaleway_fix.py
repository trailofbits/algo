"""Exercise Scaleway image selection, zone handling, and the HTTP client."""

import importlib
import json
from io import BytesIO
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import parse_qs, urlsplit

import pytest
from ansible.parsing.dataloader import DataLoader
from ansible.plugins.loader import init_plugin_loader
from ansible.template import Templar, trust_as_template
from ansible.utils.collection_loader import AnsibleCollectionConfig

ROOT = Path(__file__).resolve().parents[2]
ROLE = ROOT / "roles/cloud-scaleway"


@pytest.fixture(scope="module")
def cloud_modules():
    if not AnsibleCollectionConfig.collection_finder:
        init_plugin_loader()
    module_name = "ansible_collections.community.general.plugins.module_utils.scaleway"
    scaleway = importlib.import_module(module_name)
    manifest = Path(scaleway.__file__).parents[2] / "MANIFEST.json"
    version = json.loads(manifest.read_text())["collection_info"]["version"]
    requirements = DataLoader().load_from_file(str(ROOT / "requirements.yml"))
    expected = next(
        item["version"].removeprefix("==")
        for item in requirements["collections"]
        if item["name"] == "community.general"
    )
    assert version == expected, "Install the collections pinned in requirements.yml before testing"
    return scaleway, importlib.import_module("scaleway_compute")


@pytest.fixture
def role():
    loader = DataLoader()
    defaults = loader.load_from_file(str(ROLE / "defaults/main.yml"), trusted_as_template=True)
    tasks = loader.load_from_file(str(ROLE / "tasks/main.yml"), trusted_as_template=True)
    block = next(task["block"] for task in tasks if "block" in task)
    return loader, defaults, tasks, block


def _conditions(templar, expressions):
    trusted = (trust_as_template(f"{{{{ {expression} }}}}") for expression in expressions)
    return all(templar.template(condition) for condition in trusted)


@pytest.mark.parametrize(
    "alias,zone",
    [
        ("par1", "fr-par-1"),
        ("par2", "fr-par-2"),
        ("ams1", "nl-ams-1"),
        ("ams2", "nl-ams-2"),
        ("ams3", "nl-ams-3"),
        ("waw1", "pl-waw-1"),
        ("waw2", "pl-waw-2"),
        ("waw3", "pl-waw-3"),
    ],
)
def test_scaleway_zones_and_standalone_destroy(role, cloud_modules, alias, zone):
    scaleway, _ = cloud_modules
    loader, defaults, tasks, block = role
    for region in (alias, zone):
        variables = dict(defaults, algo_region=region)
        templar = Templar(loader=loader, variables=variables)
        selected = templar.template(tasks[1]["set_fact"])
        assert selected == {"algo_scaleway_zone": zone, "algo_scaleway_compute_alias": alias}
        variables.update(selected, scaleway_compute={"msg": {"id": "server-id"}})
        templar = Templar(loader=loader, variables=variables)
        patch = next(task["uri"] for task in block if task.get("name") == "Patch the cloud-init")
        base = f"https://api.scaleway.com/instance/v1/zones/{zone}"
        assert templar.template(patch["url"]) == f"{base}/servers/server-id/user_data/cloud-init"
        assert scaleway.SCALEWAY_LOCATION[alias]["api_endpoint"].endswith(f"/zones/{zone}")

        # destroy.yml includes these tasks directly, without loading the role defaults.
        destroy = loader.load_from_file(str(ROLE / "tasks/destroy.yml"), trusted_as_template=True)
        variables = {"playbook_dir": str(ROOT), "algo_region": region}
        templar = Templar(loader=loader, variables=variables)
        defaults_path = templar.template(destroy[0]["include_vars"])
        variables.update(loader.load_from_file(defaults_path, trusted_as_template=True))
        templar = Templar(loader=loader, variables=variables)
        assert templar.template(destroy[1]["set_fact"])["algo_scaleway_compute_alias"] == alias


@pytest.mark.parametrize("compatible,empty", [(True, False), (False, False), (False, True)])
def test_scaleway_marketplace_selection(role, compatible, empty):
    loader, defaults, _, block = role
    base = {"arch": "x86_64", "compatible_commercial_types": ["DEV1-S"], "type": "instance_sbs"}
    images = [
        dict(base, id="wrong-arch", arch="arm64"),
        dict(base, id="wrong-size", compatible_commercial_types=["DEV1-L"]),
        dict(base, id="wrong-storage", type="instance_local"),
    ]
    if compatible:
        images.append(dict(base, id="wanted"))
    if empty:
        images = []
    variables = dict(
        defaults,
        algo_scaleway_zone="nl-ams-2",
        cloud_providers={"scaleway": {"arch": "x86_64", "size": "DEV1-S"}},
        marketplace_images={"json": {"local_images": images, "total_count": len(images)}},
    )
    templar = Templar(loader=loader, variables=variables)
    url = urlsplit(templar.template(block[0]["uri"]["url"]))
    assert url.netloc == "api.scaleway.com"
    assert url.path == "/marketplace/v2/local-images"
    assert parse_qs(url.query) == {
        "image_label": ["ubuntu_jammy"],
        "zone": ["nl-ams-2"],
        "arch": ["x86_64"],
        "type": ["instance_sbs"],
        "page_size": ["100"],
    }
    variables.update(templar.template(block[1]["set_fact"]))
    templar = Templar(loader=loader, variables=variables)
    assert _conditions(templar, block[2]["assert"]["that"])
    assert _conditions(templar, block[3]["assert"]["that"]) == compatible
    if compatible:
        assert templar.template(block[4]["set_fact"])["scaleway_image_id"] == "wanted"


def test_scaleway_rejects_truncated_images(role):
    loader, _, _, block = role
    variables = {"marketplace_images": {"json": {"total_count": 101, "local_images": [{}] * 100}}}
    templar = Templar(loader=loader, variables=variables)
    check = block[2]["assert"]
    assert not _conditions(templar, check["that"])
    message = templar.template(check["fail_msg"])
    assert "truncated image list" in message
    assert "100 of 101 images" in message


@pytest.mark.parametrize("public_ip", [None, {}, {"address": ""}, {"address": "192.0.2.1"}])
def test_scaleway_waits_for_address(role, public_ip):
    loader, _, _, block = role
    start = next(task for task in block if task.get("name") == "Start the server")
    templar = Templar(loader=loader, variables={"algo_instance": {"msg": {"public_ip": public_ip}}})
    assert _conditions(templar, start["until"]) == (public_ip == {"address": "192.0.2.1"})


@pytest.fixture
def compute_module():
    def fail_json(**result):
        raise ValueError(result["msg"])

    return SimpleNamespace(
        params={
            "api_url": "https://api.scaleway.com/instance/v1/zones/nl-ams-2",
            "query_parameters": {},
            "api_token": "fixture-token",
            "api_timeout": 1,
        },
        ansible_version="test",
        jsonify=json.dumps,
        debug=lambda _message: None,
        warn=lambda _message: None,
        fail_json=fail_json,
    )


@pytest.mark.parametrize(
    "response",
    [
        (200, {"image": {"id": "wanted"}}, True),
        (404, {"message": "missing"}, False),
        (200, None, False),
        (200, [], False),
        (200, {}, False),
        (200, {"image": "unexpected"}, False),
        (200, {"image": {"id": "other"}}, False),
    ],
)
def test_scaleway_image_lookup(monkeypatch, compute_module, cloud_modules, response):
    scaleway, scaleway_compute = cloud_modules
    status, body, valid = response
    requests = []

    def fetch_url(_module, url, **kwargs):
        requests.append((urlsplit(url).path, kwargs["method"]))
        return BytesIO(json.dumps(body).encode()), {"status": status}

    monkeypatch.setattr(scaleway, "fetch_url", fetch_url)
    api = scaleway.Scaleway(compute_module)
    if valid:
        scaleway_compute.check_image_id(api, "wanted")
    else:
        with pytest.raises(ValueError, match="Cannot read Scaleway image wanted"):
            scaleway_compute.check_image_id(api, "wanted")
    assert requests == [("/instance/v1/zones/nl-ams-2/images/wanted", "GET")]


def test_scaleway_creates_selected_image(monkeypatch, compute_module, cloud_modules):
    scaleway, scaleway_compute = cloud_modules
    requests = []

    def fetch_url(_module, url, **kwargs):
        path = urlsplit(url).path
        requests.append((path, kwargs["method"], json.loads(kwargs["data"])))
        if path.endswith("/images/wanted"):
            body = {"image": {"id": "wanted"}}
        elif kwargs["method"] == "POST":
            body = {"server": {"id": "new-server"}}
        else:
            body = {"servers": []}
        return BytesIO(json.dumps(body).encode()), {"status": 200}

    monkeypatch.setattr(scaleway, "fetch_url", fetch_url)
    compute_module.params.update(
        region="ams2",
        state="present",
        image="wanted",
        name="algo",
        commercial_type="DEV1-S",
        enable_ipv6=True,
        boot_type="local",
        tags=[],
        organization="organization-id",
        security_group=None,
        public_ip="dynamic",
        wait=False,
    )
    results = []
    compute_module.check_mode = False
    compute_module.exit_json = lambda **result: results.append(result)
    scaleway_compute.core(compute_module)
    path, method, payload = requests[-1]
    assert path == "/instance/v1/zones/nl-ams-2/servers"
    assert method == "POST"
    assert payload["image"] == "wanted"
    assert payload["organization"] == "organization-id"
    assert payload["dynamic_ip_required"] is True
    assert results == [{"changed": True, "msg": {"id": "new-server"}}]
