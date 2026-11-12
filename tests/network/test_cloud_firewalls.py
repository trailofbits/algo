"""Check rendered provider requests without creating cloud resources."""

import json

import pytest
import yaml

CASES = [
    (True, True, {500, 4500, 42123}),
    (True, False, {42123}),
    (False, True, {500, 4500}),
    (False, False, set()),
    ("false", "false", set()),
]


def find_action(tasks, action):
    for task in tasks:
        if action in task:
            return task
        if "block" in task:
            found = find_action(task["block"], action)
            if found:
                return found
    return None


@pytest.mark.parametrize("scenario", CASES)
@pytest.mark.parametrize("provider", ["ec2", "lightsail", "azure"])
def test_cloud_template_ingress(ansible_loader, ansible_templar, scenario, provider):
    wireguard, ipsec, expected = scenario
    path = f"roles/cloud-{provider}"
    templar = ansible_templar(
        wireguard_enabled=wireguard,
        ipsec_enabled=ipsec,
        wireguard_port=42123,
        role_path=str(ansible_loader.get_basedir()) + "/" + path,
    )
    if provider == "azure":
        tasks = ansible_loader.load_from_file(f"{path}/tasks/main.yml", trusted_as_template=True)
        task = find_action(tasks, "azure.azcollection.azure_rm_deployment")
        document = templar.template(task["azure.azcollection.azure_rm_deployment"]["template"])
        document = json.loads(document) if isinstance(document, str) else document
        security_rules = document["resources"][0]["properties"]["securityRules"]
        rules = [rule["properties"] for rule in security_rules]
        ports = [r["destinationPortRange"] for r in rules if r["protocol"] == "Udp"]
        actual = {42123 if p == "[parameters('WireGuardPort')]" else int(p) for p in ports}
    else:
        tasks = ansible_loader.load_from_file(
            f"{path}/tasks/cloudformation.yml",
            trusted_as_template=True,
        )
        task = find_action(tasks, "cloudformation")
        # BaseLoader preserves CloudFormation tags as data; it cannot construct Python objects.
        document = yaml.load(
            templar.template(task["cloudformation"]["template_body"]),
            yaml.BaseLoader,  # noqa: S506
        )
        if provider == "ec2":
            group = document["Resources"]["InstanceSecurityGroup"]["Properties"]
            rules = group["SecurityGroupIngress"]
            ports = [r["FromPort"] for r in rules if r["IpProtocol"] == "udp"]
        else:
            rules = document["Resources"]["Instance"]["Properties"]["Networking"]["Ports"]
            ports = [r["FromPort"] for r in rules if r["Protocol"] == "udp"]
        actual = {42123 if p == "WireGuardPort" else int(p) for p in ports}
    assert actual == expected


@pytest.mark.parametrize("scenario", CASES)
@pytest.mark.parametrize("wireguard_port", [42123, 500, 4500])
@pytest.mark.parametrize(
    "provider_spec",
    [
        ("openstack", "openstack.cloud.security_group_rule", "protocol", "port_range_min"),
        ("cloudstack", "cs_securitygroup_rule", "protocol", "start_port"),
        ("vultr", "vultr.cloud.firewall_rule", "protocol", "port"),
    ],
)
def test_cloud_rule_requests(
    ansible_loader,
    ansible_templar,
    scenario,
    provider_spec,
    wireguard_port,
):
    provider, action, protocol_field, port_field = provider_spec
    wireguard, ipsec, expected = scenario
    expected = {wireguard_port if port == 42123 else port for port in expected}
    tasks = ansible_loader.load_from_file(
        f"roles/cloud-{provider}/tasks/main.yml",
        trusted_as_template=True,
    )
    task = find_action(tasks, action)
    assert task is not None
    variables = {
        "wireguard_enabled": wireguard,
        "ipsec_enabled": ipsec,
        "wireguard_port": wireguard_port,
        "algo_server_name": "test",
        "cs_security_group": {"name": "test"},
        "os_security_group": {"id": "test"},
        **task.get("vars", {}),
    }
    actual = set()
    for item in ansible_templar(**variables).template(task["loop"]):
        args = ansible_templar(item=item, **variables).template(task[action])
        if args[protocol_field] == "udp":
            port = int(args[port_field])
            assert args.get("state", "present") == ("present" if port in expected else "absent")
            if args.get("state", "present") == "present":
                actual.add(port)
    assert actual == expected


@pytest.mark.parametrize("scenario", CASES)
def test_gce_firewall_replaces_disabled_ports(ansible_loader, ansible_templar, scenario):
    wireguard, ipsec, expected = scenario
    tasks = ansible_loader.load_from_file(
        "roles/cloud-gce/tasks/main.yml",
        trusted_as_template=True,
    )
    task = find_action(tasks, "gcp_compute_firewall")
    templar = ansible_templar(
        wireguard_enabled=wireguard,
        ipsec_enabled=ipsec,
        wireguard_port=42123,
        **task.get("vars", {}),
    )
    allowed = templar.template(task["gcp_compute_firewall"]["allowed"])
    udp = [rule for rule in allowed if rule["ip_protocol"] == "udp"]
    assert all(rule["ports"] for rule in udp), "Empty GCE port lists open every UDP port"
    assert {int(port) for rule in udp for port in rule["ports"]} == expected
