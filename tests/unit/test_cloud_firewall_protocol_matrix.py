"""Protocol matrix policy for cloud and host firewalls."""

import re
from pathlib import Path

import pytest
import yaml
from jinja2 import Environment, FileSystemLoader
from jinja2.nativetypes import NativeEnvironment

ROOT = Path(__file__).parents[2]
EXPECTED = {
    (False, False): {"ssh"},
    (False, True): {"ssh", "wireguard"},
    (True, False): {"ssh", "ipsec-500", "ipsec-4500"},
    (True, True): {"ssh", "wireguard", "ipsec-500", "ipsec-4500"},
}

MANAGED_PROVIDER_FILES = (
    "roles/cloud-ec2/files/stack.yaml",
    "roles/cloud-gce/tasks/main.yml",
    "roles/cloud-cloudstack/tasks/main.yml",
    "roles/cloud-openstack/tasks/main.yml",
    "roles/cloud-vultr/tasks/main.yml",
)


def _render_host_firewall(template_name: str, ipsec: bool, wireguard: bool) -> str:
    template_dir = ROOT / "roles/common/templates"
    environment = Environment(  # nosemgrep: python.flask.security.xss.audit.direct-use-of-jinja2.direct-use-of-jinja2
        loader=FileSystemLoader(template_dir), trim_blocks=True
    )
    environment.filters["bool"] = bool
    environment.filters["ansible.utils.ipaddr"] = lambda value, _kind: value
    return environment.get_template(template_name).render(
        ipsec_enabled=ipsec,
        wireguard_enabled=wireguard,
        strongswan_network="10.19.48.0/24",
        strongswan_network_ipv6="fd9d:bc11:4021::/48",
        wireguard_network_ipv4="10.49.0.0/16",
        wireguard_network_ipv6="fd9d:bc11:4021:1::/64",
        wireguard_port=51820,
        wireguard_port_actual=51820,
        wireguard_port_avoid=53,
        reduce_mtu=0,
        ansible_default_ipv4={"interface": "eth0"},
        ansible_default_ipv6={"interface": "eth0"},
        snat_aipv4=False,
        ipv6_egress_ip="2001:db8::1",
        alternative_ingress_ip=False,
        local_service_ip="172.16.0.1",
        local_service_ipv6="fd00::1",
        ansible_ssh_port=22,
        BetweenClients_DROP=True,
        block_smb=True,
        block_netbios=True,
    )


def _host_rule_labels(rendered: str) -> set[str]:
    labels = {"ssh"}
    match = re.search(r"--dports\s+([^\s]+)", rendered)
    ports = set(match.group(1).split(",")) if match else set()
    if "500" in ports:
        labels.add("ipsec-500")
    if "4500" in ports:
        labels.add("ipsec-4500")
    if "51820" in ports:
        labels.add("wireguard")
    return labels


@pytest.mark.parametrize("template_name", ["rules.v4.j2", "rules.v6.j2"])
@pytest.mark.parametrize("ipsec,wireguard", [(False, True), (True, False), (True, True)])
def test_host_firewall_follows_protocol_matrix(template_name, ipsec, wireguard):
    rendered = _render_host_firewall(template_name, ipsec, wireguard)

    assert _host_rule_labels(rendered) == EXPECTED[(ipsec, wireguard)]
    if not ipsec:
        assert "-p esp -j ACCEPT" not in rendered
        assert "-p ah -j ACCEPT" not in rendered
        assert "-m ah -j ACCEPT" not in rendered


@pytest.mark.parametrize("path", MANAGED_PROVIDER_FILES)
def test_managed_cloud_firewalls_condition_both_protocol_families(path):
    text = (ROOT / path).read_text(encoding="utf-8")

    assert "ipsec_enabled" in text or "IpsecEnabled" in text
    assert "wireguard_enabled" in text or "WireguardEnabled" in text


def _render_native_expression(expression: str, **variables):
    environment = NativeEnvironment()
    environment.filters["bool"] = bool
    environment.filters["difference"] = lambda values, excluded: [value for value in values if value not in excluded]
    return environment.from_string(expression).render(**variables)


def _find_task(path: str, name: str):
    tasks = yaml.safe_load((ROOT / path).read_text(encoding="utf-8"))
    stack = list(tasks)
    while stack:
        task = stack.pop()
        if task.get("name") == name:
            return task
        stack.extend(task.get("block", []))
    raise AssertionError(f"No task named {name!r} in {path}")


def _disabled_loop(path: str) -> str:
    for name in (
        "Disabled protocol security rules removed",
        "Removing disabled protocol firewall rules",
    ):
        try:
            return _find_task(path, name)["loop"]
        except AssertionError:
            pass
    raise AssertionError(f"No disabled-rule task in {path}")


def test_gce_combines_enabled_udp_ports_into_one_api_entry():
    task = _find_task("roles/cloud-gce/tasks/main.yml", "Firewall configured")
    rendered = _render_native_expression(
        task["gcp_compute_firewall"]["allowed"],
        ipsec_enabled=True,
        wireguard_enabled=True,
        wireguard_port=51820,
        ssh_port=22,
    )
    udp_entries = [entry for entry in rendered if entry["ip_protocol"] == "udp"]

    assert len(udp_entries) == 1
    assert set(udp_entries[0]["ports"]) == {"500", "4500", "51820"}


@pytest.mark.parametrize(
    "path",
    [
        "roles/cloud-cloudstack/tasks/main.yml",
        "roles/cloud-openstack/tasks/main.yml",
        "roles/cloud-vultr/tasks/main.yml",
    ],
)
def test_stale_rule_cleanup_preserves_an_enabled_protocol_on_shared_port(path):
    rendered = _render_native_expression(
        _disabled_loop(path),
        ipsec_enabled=False,
        wireguard_enabled=True,
        wireguard_port=500,
    )
    removed_ports = {item["port"] for item in rendered} if rendered and isinstance(rendered[0], dict) else set(rendered)

    assert 500 not in removed_ports
    assert 4500 in removed_ports


@pytest.mark.parametrize(
    "path",
    [
        "roles/cloud-cloudstack/tasks/main.yml",
        "roles/cloud-openstack/tasks/main.yml",
        "roles/cloud-vultr/tasks/main.yml",
    ],
)
def test_rule_managed_providers_revoke_disabled_protocol_rules(path):
    text = (ROOT / path).read_text(encoding="utf-8")

    assert "state: absent" in text
    assert "not ipsec_enabled" in text
    assert "not wireguard_enabled" in text


def test_ec2_uses_inline_conditionals_for_update_safe_ingress():
    text = (ROOT / "roles/cloud-ec2/files/stack.yaml").read_text(encoding="utf-8")

    assert "OpenIpsecPorts" in text
    assert "OpenWireguardPorts" in text
    assert "Type: AWS::EC2::SecurityGroupIngress" not in text
    assert text.count("AWS::NoValue") >= 3


def test_input_rejects_both_protocols_disabled():
    text = (ROOT / "input.yml").read_text(encoding="utf-8")

    assert "At least one VPN protocol must be enabled" in text
    assert "ipsec_enabled | bool or wireguard_enabled | bool" in text
    assert "WireGuard port must not overlap IPsec UDP ports 500 or 4500" in text
    assert "wireguard_port | int not in [500, 4500]" in text
