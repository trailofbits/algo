"""Exercise Scaleway image selection, zone handling, and the HTTP client."""

from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import pytest
from ansible.parsing.dataloader import DataLoader
from ansible.template import Templar, trust_as_template

ROOT = Path(__file__).resolve().parents[2]
ROLE = ROOT / "roles/cloud-scaleway"


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
def test_scaleway_zones_and_standalone_destroy(role, alias, zone):
    loader, defaults, tasks, block = role
    for region in (alias, zone):
        variables = dict(defaults, algo_region=region)
        templar = Templar(loader=loader, variables=variables)
        selected = templar.template(tasks[1]["set_fact"])
        assert selected == {"algo_scaleway_zone": zone}
        variables.update(selected, scaleway_created={"server": {"id": "server-id"}})
        templar = Templar(loader=loader, variables=variables)
        patch = next(task["uri"] for task in block if task.get("name") == "Patch the cloud-init")
        base = f"https://api.scaleway.com/instance/v1/zones/{zone}"
        assert templar.template(patch["url"]) == f"{base}/servers/server-id/user_data/cloud-init"

        # destroy.yml includes these tasks directly, without loading the role defaults.
        destroy = loader.load_from_file(str(ROLE / "tasks/destroy.yml"), trusted_as_template=True)
        variables = {"playbook_dir": str(ROOT), "algo_region": region}
        templar = Templar(loader=loader, variables=variables)
        defaults_path = templar.template(destroy[0]["include_vars"])
        variables.update(loader.load_from_file(defaults_path, trusted_as_template=True))
        templar = Templar(loader=loader, variables=variables)
        assert templar.template(destroy[1]["set_fact"])["algo_scaleway_zone"] == zone


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


@pytest.mark.parametrize(
    "public_ips,ready",
    [
        (None, False),
        ([], False),
        ([{"family": "inet", "address": ""}], False),
        ([{"family": "inet6", "address": "2001:db8::1"}], False),
        ([{"family": "inet6", "address": "2001:db8::1"}, {"family": "inet", "address": "192.0.2.1"}], True),
    ],
)
def test_scaleway_waits_for_address(role, public_ips, ready):
    loader, _, tasks, block = role
    start = next(task for task in block if task.get("name") == "Start the server")
    variables = {"algo_instance": {"server": {"public_ips": public_ips}}}
    templar = Templar(loader=loader, variables=variables)
    assert _conditions(templar, start["until"]) == ready
    if ready:
        assert templar.template(tasks[-1]["set_fact"]["cloud_instance_ip"]) == "192.0.2.1"
