# fmt: off
# ruff: noqa: W191
"""Tests for Oracle Cloud provider provisioning and cleanup."""

from pathlib import Path

import yaml

ROOT = Path(__file__).parents[2]


def load_yaml(path):
	"""Load a YAML file from the repository root."""
	return yaml.safe_load((ROOT / path).read_text())


def flatten_tasks(tasks):
	"""Yield tasks nested inside Ansible blocks too."""
	for task in tasks:
		yield task
		yield from flatten_tasks(task.get('block', []))


def test_oracle_collection_is_declared():
	"""Oracle deployments need the official OCI Ansible collection."""
	collections = load_yaml('requirements.yml')['collections']
	oracle = next(item for item in collections if item['name'] == 'oracle.oci')

	assert oracle['version'] == '==5.5.0'


def test_oracle_sdk_is_installed_without_a_project_extra():
	"""Oracle installs the SDK directly because it has no project optional extra."""
	prompts = load_yaml('roles/cloud-oracle/tasks/prompts.yml')
	sdk_task = next(task for task in prompts if task['name'] == 'Install the Oracle Cloud Infrastructure Python SDK')
	assert sdk_task['command']['argv'][-1] == 'oci>=2.152.1'

	cloud_pre = load_yaml('playbooks/cloud-pre.yml')
	dependency_task = next(task for task in cloud_pre[0]['block'] if task['name'] == 'Install cloud provider dependencies')
	assert 'oracle' in str(dependency_task['when'])


def test_oracle_provider_is_offered_in_the_menu():
	"""The provider menu must select the cloud-oracle role."""
	input_yml = (ROOT / 'input.yml').read_text()

	assert 'alias: oracle' in input_yml


def test_oracle_network_opens_algo_ports():
	"""Oracle's network security list must expose SSH and both VPN protocols."""
	tasks = load_yaml('roles/cloud-oracle/tasks/main.yml')
	security_task = next(task for task in tasks if task['name'] == 'Create Oracle security list')
	rules = security_task['oracle.oci.oci_network_security_list']['ingress_security_rules']
	udp_ports = [rule['udp_options']['destination_port_range']['min'] for rule in rules if 'udp_options' in rule]

	assert udp_ports == [500, 4500, '{{ wireguard_port | int }}']
	assert rules[0]['tcp_options']['destination_port_range']['min'] == '{{ ssh_port | int }}'


def test_oracle_allows_time_for_cloud_init_before_ssh_is_ready():
	"""Ubuntu package upgrades can delay Oracle's custom SSH port for several minutes."""
	cloud_post = load_yaml('playbooks/cloud-post.yml')
	wait_task = next(task for task in cloud_post if task['name'] == 'Wait until SSH becomes ready...')
	oracle_tasks = load_yaml('roles/cloud-oracle/tasks/main.yml')
	connection_task = next(task for task in oracle_tasks if task['name'] == 'Set Oracle VM connection details')

	assert wait_task['wait_for']['timeout'] == '{{ cloud_init_ssh_timeout | default(320) }}'
	assert connection_task['set_fact']['cloud_init_ssh_timeout'] == 1200


def test_oracle_destroy_removes_instance_and_network():
	"""Destroy tasks must remove the VM and its owned VCN resources."""
	tasks = list(flatten_tasks(load_yaml('roles/cloud-oracle/tasks/destroy.yml')))
	task_names = {task['name'] for task in tasks}

	assert 'Destroy Oracle VM' in task_names
	assert 'Remove Oracle subnet' in task_names
	assert 'Remove Oracle route table' in task_names
	assert 'Remove Oracle Internet Gateway' in task_names
	assert 'Remove Oracle security list' in task_names
	assert 'Remove Oracle VCN' in task_names


def test_oracle_settings_are_saved_for_destroy():
	"""The saved server config needs its OCI profile and compartment to clean up."""
	server_yml = (ROOT / 'server.yml').read_text()
	destroy_yml = (ROOT / 'destroy.yml').read_text()

	assert 'algo_oci_compartment_id' in server_yml
	assert 'oci_config_profile' in server_yml
	assert 'oci_compartment_id: "{{ _server_cfg.algo_oci_compartment_id }}"' in destroy_yml
