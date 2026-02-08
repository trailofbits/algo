"""Tests for the destroy playbook and provider destroy task files."""

import os
import subprocess

import yaml  # type: ignore[import-untyped]

PROVIDERS = [
    "digitalocean",
    "ec2",
    "lightsail",
    "azure",
    "gce",
    "hetzner",
    "vultr",
    "scaleway",
    "openstack",
    "cloudstack",
    "linode",
]

REGION_REQUIRED_PROVIDERS = ["ec2", "lightsail", "gce", "scaleway", "vultr"]


def test_destroy_playbook_exists():
    """destroy.yml must exist at repo root."""
    assert os.path.exists("destroy.yml"), "destroy.yml not found"


def test_destroy_playbook_valid_yaml():
    """destroy.yml must be valid YAML."""
    with open("destroy.yml") as f:
        data = yaml.safe_load(f)
    assert isinstance(data, list), "destroy.yml should be a YAML list"
    assert len(data) == 1, "destroy.yml should have one play"
    play = data[0]
    assert play["hosts"] == "localhost"
    assert play["gather_facts"] is False


def test_destroy_playbook_syntax():
    """destroy.yml must pass ansible-playbook --syntax-check."""
    result = subprocess.run(
        ["ansible-playbook", "destroy.yml", "--syntax-check"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Syntax check failed:\n{result.stderr}"


def test_destroy_playbook_has_rescue():
    """destroy.yml must include a rescue block for error handling."""
    with open("destroy.yml") as f:
        content = f.read()
    assert "rescue:" in content
    assert "rescue.yml" in content


def test_destroy_playbook_has_confirmation():
    """destroy.yml must have a confirmation step."""
    with open("destroy.yml") as f:
        content = f.read()
    assert "confirm" in content.lower()


def test_all_provider_destroy_files_exist():
    """Every cloud provider must have a destroy.yml task file."""
    for provider in PROVIDERS:
        path = f"roles/cloud-{provider}/tasks/destroy.yml"
        assert os.path.exists(path), f"Missing destroy task file: {path}"


def test_all_provider_destroy_files_valid_yaml():
    """Every provider destroy.yml must be valid YAML."""
    for provider in PROVIDERS:
        path = f"roles/cloud-{provider}/tasks/destroy.yml"
        with open(path) as f:
            data = yaml.safe_load(f)
        assert isinstance(data, list), f"{path} should be a YAML list"


def test_provider_destroy_uses_absent_state():
    """Each provider destroy file must use state: absent (or expunged)."""
    for provider in PROVIDERS:
        path = f"roles/cloud-{provider}/tasks/destroy.yml"
        with open(path) as f:
            content = f.read()
        assert "absent" in content or "expunged" in content, f"{path} missing state: absent/expunged"


def test_ec2_destroy_uses_cloudformation():
    """EC2 destroy should delete the CloudFormation stack."""
    with open("roles/cloud-ec2/tasks/destroy.yml") as f:
        content = f.read()
    assert "cloudformation" in content
    assert "stack_name" in content


def test_lightsail_destroy_uses_cloudformation():
    """Lightsail destroy should delete the CloudFormation stack."""
    with open("roles/cloud-lightsail/tasks/destroy.yml") as f:
        content = f.read()
    assert "cloudformation" in content
    assert "stack_name" in content


def test_gce_destroy_cleans_subsidiary_resources():
    """GCE destroy should clean up firewall, static IP, and network."""
    with open("roles/cloud-gce/tasks/destroy.yml") as f:
        content = f.read()
    assert "gcp_compute_firewall" in content
    assert "gcp_compute_address" in content
    assert "gcp_compute_network" in content


def test_vultr_destroy_cleans_firewall_group():
    """Vultr destroy should remove the firewall group."""
    with open("roles/cloud-vultr/tasks/destroy.yml") as f:
        content = f.read()
    assert "firewall_group" in content


def test_openstack_destroy_cleans_security_group():
    """OpenStack destroy should remove the security group."""
    with open("roles/cloud-openstack/tasks/destroy.yml") as f:
        content = f.read()
    assert "security_group" in content


def test_cloudstack_destroy_cleans_security_group():
    """CloudStack destroy should remove the security group."""
    with open("roles/cloud-cloudstack/tasks/destroy.yml") as f:
        content = f.read()
    assert "security_group" in content


def test_subsidiary_cleanup_is_best_effort():
    """Subsidiary resource cleanup should use failed_when: false."""
    files_with_subsidiary = {
        "gce": ["gcp_compute_address", "gcp_compute_firewall", "gcp_compute_network"],
        "vultr": ["firewall_group"],
        "openstack": ["security_group"],
        "cloudstack": ["security_group"],
    }
    for provider, _resources in files_with_subsidiary.items():
        path = f"roles/cloud-{provider}/tasks/destroy.yml"
        with open(path) as f:
            content = f.read()
        assert "failed_when: false" in content, f"{path} should use failed_when: false for subsidiary cleanup"


def test_linode_uses_label_not_name():
    """Linode module uses 'label' parameter, not 'name'."""
    with open("roles/cloud-linode/tasks/destroy.yml") as f:
        content = f.read()
    assert "label:" in content, "Linode destroy should use 'label' parameter"


def test_azure_deletes_resource_group():
    """Azure destroy should delete the entire resource group."""
    with open("roles/cloud-azure/tasks/destroy.yml") as f:
        content = f.read()
    assert "azure_rm_resourcegroup" in content
    assert "force_delete_nonempty" in content


def test_algo_script_has_destroy_command():
    """The algo shell script must include the destroy subcommand."""
    with open("algo") as f:
        content = f.read()
    assert "destroy)" in content
    assert "destroy.yml" in content


def test_algo_script_destroy_requires_ip():
    """The destroy command should validate that an IP is provided."""
    with open("algo") as f:
        content = f.read()
    assert "server_ip=$2" in content


def test_server_yml_stores_algo_region():
    """server.yml should store algo_region in .config.yml."""
    with open("server.yml") as f:
        content = f.read()
    assert "algo_region" in content


def test_destroy_playbook_validates_region_for_required_providers():
    """destroy.yml must check region for ec2/lightsail/gce/scaleway."""
    with open("destroy.yml") as f:
        content = f.read()
    for provider in REGION_REQUIRED_PROVIDERS:
        assert provider in content, f"destroy.yml should reference {provider} in region validation"


def test_destroy_playbook_loads_server_config():
    """destroy.yml must load .config.yml from the configs directory."""
    with open("destroy.yml") as f:
        content = f.read()
    assert ".config.yml" in content
    assert "include_vars" in content
