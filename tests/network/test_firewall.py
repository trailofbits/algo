"""Validate the rendered host firewall for every supported protocol combination."""

import shlex
import shutil
import subprocess

import pytest
from ansible.template import trust_as_template

CASES = [
    (True, True, {500, 4500, 51820}, {1, 2}),
    (True, False, {51820}, {1}),
    (False, True, {500, 4500}, {2}),
    (False, False, set(), set()),
    ("false", "false", set(), set()),
]


@pytest.mark.parametrize("scenario", CASES)
@pytest.mark.parametrize("family", [4, 6])
def test_firewall_protocols_and_dns(ansible_templar, scenario, family):
    wireguard, ipsec, ports, networks = scenario
    templar = ansible_templar(wireguard_enabled=wireguard, ipsec_enabled=ipsec)
    expression = f"{{{{ lookup('template', 'roles/common/templates/rules.v{family}.j2') }}}}"
    content = templar.template(trust_as_template(expression))
    rules = [shlex.split(line) for line in content.splitlines() if line.startswith("-A ")]
    allowed_ports = set()
    dns_sources = {"tcp": set(), "udp": set()}
    for rule in rules:
        for option in ("-s", "-d", "--dports", "--dport"):
            if option in rule:
                assert not rule[rule.index(option) + 1].startswith("-"), rule
        if rule[:2] != ["-A", "INPUT"] or rule[-2:] != ["-j", "ACCEPT"]:
            continue
        if "--dports" in rule:
            allowed_ports.update(map(int, rule[rule.index("--dports") + 1].split(",")))
        if "--dport" in rule and rule[rule.index("--dport") + 1] == "53":
            protocol = rule[rule.index("-p") + 1]
            sources = rule[rule.index("-s") + 1].split(",")
            dns_sources[protocol].update(sources)
    assert allowed_ports == ports
    expected = {f"10.{n}.0.0/24" if family == 4 else f"fd0{n}::/64" for n in networks}
    assert dns_sources == {"tcp": expected, "udp": expected}


@pytest.mark.parametrize("scenario", CASES)
@pytest.mark.parametrize("family", [4, 6])
def test_firewall_restore(network_runtime, ansible_templar, scenario, family):
    wireguard, ipsec, _, _ = scenario
    templar = ansible_templar(wireguard_enabled=wireguard, ipsec_enabled=ipsec)
    expression = f"{{{{ lookup('template', 'roles/common/templates/rules.v{family}.j2') }}}}"
    content = templar.template(trust_as_template(expression))
    binary = "iptables-restore" if family == 4 else "ip6tables-restore"
    assert shutil.which(binary), f"Install {binary} in the network test container"
    result = subprocess.run(
        [binary, "--test"],
        input=content,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize("family", [4, 6])
def test_wireguard_dns_port_redirection(ansible_templar, family):
    templar = ansible_templar(wireguard_port=53, wireguard_enabled=True, ipsec_enabled=False)
    expression = f"{{{{ lookup('template', 'roles/common/templates/rules.v{family}.j2') }}}}"
    content = templar.template(trust_as_template(expression))
    assert "--dports 53,51820 -j ACCEPT" in content
    assert "--dport 53 -j REDIRECT --to-port 51820" in content
