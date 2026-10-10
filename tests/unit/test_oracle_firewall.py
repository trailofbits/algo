# fmt: off
# ruff: noqa: W191
"""Preserve OCI storage protections while replacing the guest VPN firewall."""

from pathlib import Path

import pytest
import yaml
from jinja2 import Environment, FileSystemLoader, StrictUndefined

ROOT = Path(__file__).parents[2]

# Mock an OCI image's active filter table, including its root-only iSCSI rule.
# A second endpoint checks that preservation does not hardcode Oracle addresses.
ORACLE_FILTER = '''*filter
:INPUT ACCEPT [0:0]
:FORWARD ACCEPT [0:0]
:OUTPUT ACCEPT [0:0]
:InstanceServices - [0:0]
-A INPUT -p tcp -m tcp --dport 22 -j ACCEPT
-A INPUT -j REJECT --reject-with icmp-host-prohibited
-A FORWARD -j REJECT --reject-with icmp-host-prohibited
-A OUTPUT -d 169.254.0.0/16 -j InstanceServices
-A InstanceServices -d 169.254.0.2/32 -p tcp -m owner --uid-owner 0 -m tcp --dport 3260 -j ACCEPT
-A InstanceServices -d 169.254.2.0/24 -p tcp -m owner --uid-owner 0 -m tcp --dport 3260 -j ACCEPT
-A InstanceServices -d 169.254.169.254/32 -p udp -m udp --dport 53 -j ACCEPT
-A InstanceServices -d 169.254.77.0/24 -p tcp -m owner --uid-owner 0 -m tcp --dport 4321 -j ACCEPT
-A InstanceServices -d 169.254.0.0/16 -p tcp -m comment --comment "Protect boot and block volumes" -j REJECT --reject-with tcp-reset
-A InstanceServices -d 169.254.0.0/16 -p udp -j REJECT --reject-with icmp-port-unreachable
COMMIT
'''


@pytest.fixture
def firewall_environment():
	"""Load the production template with strict variable handling."""
	environment = Environment(
		loader=FileSystemLoader(ROOT / 'roles/common/templates'),
		undefined=StrictUndefined,
	)
	environment.filters['bool'] = bool
	return environment


def render_firewall(environment, provider='oracle', saved_rules=ORACLE_FILTER):
	"""Render the real VPN firewall against an active image rules fixture."""
	return environment.get_template('rules.v4.j2').render(
		algo_provider=provider,
		_oracle_iptables_filter={'stdout_lines': saved_rules.splitlines()},
		ipsec_enabled=False,
		wireguard_enabled=True,
		wireguard_network_ipv4='10.49.0.0/16',
		wireguard_port=51820,
		wireguard_port_avoid=53,
		wireguard_port_actual=51820,
		ansible_default_ipv4={'interface': 'ens3'},
		snat_aipv4=False,
		BetweenClients_DROP=True,
		block_smb=True,
		block_netbios=True,
		local_service_ip='10.49.0.1',
		ansible_ssh_port=4160,
		reduce_mtu=0,
	)


def test_oracle_storage_rules_survive_firewall_replacement(firewall_environment):
	"""Keep every service exception and rejection in its original order."""
	rendered = render_firewall(firewall_environment)
	expected = [line for line in ORACLE_FILTER.splitlines() if line.startswith('-A InstanceServices ')]
	actual = [line for line in rendered.splitlines() if line.startswith('-A InstanceServices ')]

	assert actual == expected
	assert ':InstanceServices - [0:0]' in rendered
	assert rendered.index(':InstanceServices ') < rendered.index('-A OUTPUT -d 169.254.0.0/16 -j InstanceServices')
	assert '-A INPUT -p tcp --dport 4160 -m conntrack --ctstate NEW -j ACCEPT' in rendered
	assert '-A INPUT -j REJECT --reject-with icmp-host-prohibited' not in rendered
	assert '-A FORWARD -j REJECT --reject-with icmp-host-prohibited' not in rendered


def test_oracle_services_cannot_bypass_tunnel_isolation(firewall_environment):
	"""An SSH tunnel must be denied before an OCI service can accept it."""
	rendered = render_firewall(firewall_environment)
	tunnel_drop = '-A OUTPUT -d 169.254.0.0/16 -m owner --gid-owner 15000 -j DROP'
	service_jump = '-A OUTPUT -d 169.254.0.0/16 -j InstanceServices'

	assert rendered.index(tunnel_drop) < rendered.index(service_jump)
	assert '-A FORWARD -s 10.49.0.0/16 -d 169.254.0.0/16 -j DROP' in rendered


def test_oracle_firewall_repeated_install_does_not_duplicate_rules(firewall_environment):
	"""Capturing an already installed Algo firewall must render the same rules."""
	first = render_firewall(firewall_environment)
	second = render_firewall(firewall_environment, saved_rules=first)

	assert first == second
	assert second.count(':InstanceServices - [0:0]') == 1
	assert second.count('-A OUTPUT -d 169.254.0.0/16 -j InstanceServices') == 1


def test_other_providers_ignore_oracle_image_rules(firewall_environment):
	"""Oracle data left in a variable must not affect another cloud's firewall."""
	rendered = render_firewall(firewall_environment, provider='ec2')

	assert 'InstanceServices' not in rendered
	assert rendered == render_firewall(firewall_environment, provider='ec2', saved_rules='')


@pytest.mark.parametrize(('provider', 'use_legacy'), [('oracle', False), ('ec2', True)])
def test_oracle_keeps_the_active_iptables_backend(firewall_environment, provider, use_legacy):
	"""Changing backends can leave OCI's rejecting rules active in parallel."""
	tasks = yaml.safe_load((ROOT / 'roles/common/tasks/ubuntu.yml').read_text())
	legacy_task = next(task for task in tasks if task.get('name') == 'Ubuntu 22.04+ | Use iptables-legacy for compatibility')
	conditions = legacy_task['when']
	if isinstance(conditions, str):
		conditions = [conditions]
	will_run = all(
		firewall_environment.compile_expression(condition)(algo_provider=provider, is_ubuntu_22_plus=True)
		for condition in conditions
	)

	assert will_run is use_legacy


def test_image_rules_are_captured_before_installing_the_template(firewall_environment):
	"""Read the active backend before replacing the persistent configuration."""
	tasks = yaml.safe_load((ROOT / 'roles/common/tasks/iptables.yml').read_text())
	capture = next(task for task in tasks if task.get('register') == '_oracle_iptables_filter')
	template = next(task for task in tasks if 'template' in task)

	assert tasks.index(capture) < tasks.index(template)
	assert capture['command']['argv'] == ['iptables-save', '-t', 'filter']
	assert capture['changed_when'] is False
	assert capture['check_mode'] is False
	condition = firewall_environment.compile_expression(capture['when'])
	assert condition(algo_provider='oracle') is True
	assert condition(algo_provider='ec2') is False
