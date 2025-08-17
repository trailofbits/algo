#!/usr/bin/env python3
"""
Test iptables rules logic for VPN traffic routing.

These tests verify that the iptables rules templates generate correct
NAT rules for both WireGuard and IPsec VPN traffic.
"""

from pathlib import Path

import pytest
from jinja2 import Environment, FileSystemLoader


def load_template(template_name):
    """Load a Jinja2 template from the roles/common/templates directory."""
    template_dir = Path(__file__).parent.parent.parent / "roles" / "common" / "templates"
    env = Environment(loader=FileSystemLoader(str(template_dir)))
    return env.get_template(template_name)


def test_wireguard_nat_rules_ipv4():
    """Test that WireGuard traffic gets proper NAT rules without policy matching."""
    template = load_template("rules.v4.j2")

    # Test with WireGuard enabled
    result = template.render(
        ipsec_enabled=False,
        wireguard_enabled=True,
        wireguard_network_ipv4="10.49.0.0/16",
        wireguard_port=51820,
        wireguard_port_avoid=53,
        wireguard_port_actual=51820,
        ansible_default_ipv4={"interface": "eth0"},
        snat_aipv4=None,
        BetweenClients_DROP=True,
        block_smb=True,
        block_netbios=True,
        local_service_ip="10.49.0.1",
        ansible_ssh_port=22,
        reduce_mtu=0,
    )

    # Verify NAT rule exists with output interface and without policy matching
    assert "-A POSTROUTING -s 10.49.0.0/16 -o eth0 -j MASQUERADE" in result
    # Verify no policy matching in WireGuard NAT rules
    assert "-A POSTROUTING -s 10.49.0.0/16 -m policy" not in result


def test_ipsec_nat_rules_ipv4():
    """Test that IPsec traffic gets proper NAT rules without policy matching."""
    template = load_template("rules.v4.j2")

    # Test with IPsec enabled
    result = template.render(
        ipsec_enabled=True,
        wireguard_enabled=False,
        strongswan_network="10.48.0.0/16",
        strongswan_network_ipv6="2001:db8::/48",
        ansible_default_ipv4={"interface": "eth0"},
        snat_aipv4=None,
        BetweenClients_DROP=True,
        block_smb=True,
        block_netbios=True,
        local_service_ip="10.48.0.1",
        ansible_ssh_port=22,
        reduce_mtu=0,
    )

    # Verify NAT rule exists with output interface and without policy matching
    assert "-A POSTROUTING -s 10.48.0.0/16 -o eth0 -j MASQUERADE" in result
    # Verify no policy matching in IPsec NAT rules (this was the bug)
    assert "-A POSTROUTING -s 10.48.0.0/16 -m policy --pol none" not in result


def test_both_vpns_nat_rules_ipv4():
    """Test NAT rules when both VPN types are enabled."""
    template = load_template("rules.v4.j2")

    result = template.render(
        ipsec_enabled=True,
        wireguard_enabled=True,
        strongswan_network="10.48.0.0/16",
        wireguard_network_ipv4="10.49.0.0/16",
        strongswan_network_ipv6="2001:db8::/48",
        wireguard_network_ipv6="2001:db8:a160::/48",
        wireguard_port=51820,
        wireguard_port_avoid=53,
        wireguard_port_actual=51820,
        ansible_default_ipv4={"interface": "eth0"},
        snat_aipv4=None,
        BetweenClients_DROP=True,
        block_smb=True,
        block_netbios=True,
        local_service_ip="10.49.0.1",
        ansible_ssh_port=22,
        reduce_mtu=0,
    )

    # Both should have NAT rules with output interface
    assert "-A POSTROUTING -s 10.48.0.0/16 -o eth0 -j MASQUERADE" in result
    assert "-A POSTROUTING -s 10.49.0.0/16 -o eth0 -j MASQUERADE" in result

    # Neither should have policy matching
    assert "-m policy --pol none" not in result


def test_alternative_ingress_snat():
    """Test that alternative ingress IP uses SNAT instead of MASQUERADE."""
    template = load_template("rules.v4.j2")

    result = template.render(
        ipsec_enabled=True,
        wireguard_enabled=True,
        strongswan_network="10.48.0.0/16",
        wireguard_network_ipv4="10.49.0.0/16",
        strongswan_network_ipv6="2001:db8::/48",
        wireguard_network_ipv6="2001:db8:a160::/48",
        wireguard_port=51820,
        wireguard_port_avoid=53,
        wireguard_port_actual=51820,
        ansible_default_ipv4={"interface": "eth0"},
        snat_aipv4="192.168.1.100",  # Alternative ingress IP
        BetweenClients_DROP=True,
        block_smb=True,
        block_netbios=True,
        local_service_ip="10.49.0.1",
        ansible_ssh_port=22,
        reduce_mtu=0,
    )

    # Should use SNAT with specific IP and output interface instead of MASQUERADE
    assert "-A POSTROUTING -s 10.48.0.0/16 -o eth0 -j SNAT --to 192.168.1.100" in result
    assert "-A POSTROUTING -s 10.49.0.0/16 -o eth0 -j SNAT --to 192.168.1.100" in result
    assert "MASQUERADE" not in result


def test_ipsec_forward_rule_has_policy_match():
    """Test that IPsec FORWARD rules still use policy matching (this is correct)."""
    template = load_template("rules.v4.j2")

    result = template.render(
        ipsec_enabled=True,
        wireguard_enabled=False,
        strongswan_network="10.48.0.0/16",
        strongswan_network_ipv6="2001:db8::/48",
        ansible_default_ipv4={"interface": "eth0"},
        snat_aipv4=None,
        BetweenClients_DROP=True,
        block_smb=True,
        block_netbios=True,
        local_service_ip="10.48.0.1",
        ansible_ssh_port=22,
        reduce_mtu=0,
    )

    # FORWARD rule should have policy match (this is correct and should stay)
    assert "-A FORWARD -m conntrack --ctstate NEW -s 10.48.0.0/16 -m policy --pol ipsec --dir in -j ACCEPT" in result


def test_wireguard_forward_rule_no_policy_match():
    """Test that WireGuard FORWARD rules don't use policy matching."""
    template = load_template("rules.v4.j2")

    result = template.render(
        ipsec_enabled=False,
        wireguard_enabled=True,
        wireguard_network_ipv4="10.49.0.0/16",
        wireguard_port=51820,
        wireguard_port_avoid=53,
        wireguard_port_actual=51820,
        ansible_default_ipv4={"interface": "eth0"},
        snat_aipv4=None,
        BetweenClients_DROP=True,
        block_smb=True,
        block_netbios=True,
        local_service_ip="10.49.0.1",
        ansible_ssh_port=22,
        reduce_mtu=0,
    )

    # WireGuard FORWARD rule should NOT have any policy match
    assert "-A FORWARD -m conntrack --ctstate NEW -s 10.49.0.0/16 -j ACCEPT" in result
    assert "-A FORWARD -m conntrack --ctstate NEW -s 10.49.0.0/16 -m policy" not in result


def test_output_interface_in_nat_rules():
    """Test that output interface is specified in NAT rules."""
    template = load_template("rules.v4.j2")

    result = template.render(
        snat_aipv4=False,
        wireguard_enabled=True,
        ipsec_enabled=True,
        wireguard_network_ipv4="10.49.0.0/16",
        strongswan_network="10.48.0.0/16",
        ansible_default_ipv4={"interface": "eth0", "address": "10.0.0.1"},
        ansible_default_ipv6={"interface": "eth0", "address": "fd9d:bc11:4020::1"},
        wireguard_port_actual=51820,
        wireguard_port_avoid=53,
        wireguard_port=51820,
        ansible_ssh_port=22,
        reduce_mtu=0,
    )

    # Check that output interface is specified for both VPNs
    assert "-A POSTROUTING -s 10.49.0.0/16 -o eth0 -j MASQUERADE" in result
    assert "-A POSTROUTING -s 10.48.0.0/16 -o eth0 -j MASQUERADE" in result

    # Ensure we don't have rules without output interface
    assert "-A POSTROUTING -s 10.49.0.0/16 -j MASQUERADE" not in result
    assert "-A POSTROUTING -s 10.48.0.0/16 -j MASQUERADE" not in result


def test_dns_firewall_restricted_to_vpn():
    """Test that DNS access is restricted to VPN clients only."""
    template = load_template("rules.v4.j2")

    result = template.render(
        ipsec_enabled=True,
        wireguard_enabled=True,
        strongswan_network="10.48.0.0/16",
        wireguard_network_ipv4="10.49.0.0/16",
        strongswan_network_ipv6="2001:db8::/48",
        wireguard_network_ipv6="2001:db8:a160::/48",
        wireguard_port=51820,
        wireguard_port_avoid=53,
        wireguard_port_actual=51820,
        ansible_default_ipv4={"interface": "eth0"},
        snat_aipv4=None,
        BetweenClients_DROP=True,
        block_smb=True,
        block_netbios=True,
        local_service_ip="172.23.198.242",
        ansible_ssh_port=22,
        reduce_mtu=0,
    )

    # DNS should only be accessible from VPN subnets
    assert "-A INPUT -s 10.48.0.0/16,10.49.0.0/16 -d 172.23.198.242 -p udp --dport 53 -j ACCEPT" in result
    # Should NOT have unrestricted DNS access
    assert "-A INPUT -d 172.23.198.242 -p udp --dport 53 -j ACCEPT" not in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
