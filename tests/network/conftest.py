"""Render production networking configuration with Ansible's own filters."""

import os
from pathlib import Path

import pytest
from ansible.parsing.dataloader import DataLoader
from ansible.template import Templar

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def network_runtime():
    if os.environ.get("ALGO_NETWORK_RUNTIME") != "1":
        pytest.skip("Set ALGO_NETWORK_RUNTIME=1 in the network test container")


@pytest.fixture
def ansible_loader():
    loader = DataLoader()
    loader.set_basedir(str(ROOT))
    return loader


@pytest.fixture
def ansible_templar(ansible_loader):
    def make(**variables):
        defaults = ansible_loader.load_from_file(str(ROOT / "config.cfg"), trusted_as_template=True)
        defaults.update(
            ansible_facts={
                "default_ipv4": {"interface": "eth0"},
                "default_ipv6": {"interface": "eth0"},
            },
            ansible_ssh_port=4160,
            wireguard_port_avoid=53,
            wireguard_port_actual=51820,
            wireguard_network_ipv4="10.1.0.0/24",
            wireguard_network_ipv6="fd01::/64",
            strongswan_network="10.2.0.0/24",
            strongswan_network_ipv6="fd02::/64",
            local_service_ip="172.16.0.1",
            local_service_ipv6="fd00::1",
            snat_aipv4=False,
            alternative_ingress_ip=False,
            reduce_mtu=0,
        )
        defaults.update(variables)
        return Templar(loader=ansible_loader, variables=defaults)

    return make
