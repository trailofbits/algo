from pathlib import Path

import yaml

ROOT = Path(__file__).parents[2]
GROUNDED_SELECTORS = {
    "digitalocean": {"22.04": "ubuntu-22-04-x64", "24.04": "ubuntu-24-04-x64"},
    "ec2": {"22.04": "ubuntu-jammy-22.04", "24.04": "ubuntu-noble-24.04"},
    "gce": {"22.04": "ubuntu-2204-lts", "24.04": "ubuntu-2404-lts-amd64"},
    "scaleway": {"22.04": "ubuntu_jammy", "24.04": "ubuntu_noble"},
    "hetzner": {"22.04": "ubuntu-22.04", "24.04": "ubuntu-24.04"},
    "vultr": {"22.04": "Ubuntu 22.04 LTS x64", "24.04": "Ubuntu 24.04 LTS x64"},
    "linode": {"22.04": "linode/ubuntu22.04", "24.04": "linode/ubuntu24.04"},
}
UNVERIFIED_24_04 = {"openstack", "cloudstack"}
EXCLUDED_PROVIDERS = {"azure", "lightsail"}


def _config():
    return yaml.safe_load((ROOT / "config.cfg").read_text())


def test_ubuntu_version_defaults_to_transition_release_and_has_exact_allowlist():
    config = _config()
    assert config["ubuntu_version"] == "22.04"
    assert config["supported_ubuntu_versions"] == ["22.04", "24.04"]


def test_grounded_provider_native_selectors_cover_both_supported_releases():
    providers = _config()["cloud_providers"]
    for provider, expected in GROUNDED_SELECTORS.items():
        image = providers[provider]["os" if provider == "vultr" else "image"]
        if provider == "ec2":
            image = image["name"]
        assert image == expected


def test_excluded_providers_are_never_validated_as_supported():
    config = _config()
    support = config["cloud_provider_ubuntu_versions"]
    for provider in EXCLUDED_PROVIDERS:
        assert support[provider] == []


def test_tenant_or_catalog_specific_24_04_images_are_not_advertised():
    config = _config()
    support = config["cloud_provider_ubuntu_versions"]
    for provider in UNVERIFIED_24_04:
        assert support[provider] == ["22.04"]
        assert "24.04" not in config["cloud_providers"][provider].get("image", {})


def test_image_consumers_select_the_requested_ubuntu_version():
    task_files = {
        "digitalocean": "roles/cloud-digitalocean/tasks/main.yml",
        "ec2": "roles/cloud-ec2/tasks/main.yml",
        "gce": "roles/cloud-gce/tasks/main.yml",
        "scaleway": "roles/cloud-scaleway/tasks/main.yml",
        "hetzner": "roles/cloud-hetzner/tasks/main.yml",
        "linode": "roles/cloud-linode/tasks/main.yml",
    }
    for provider, path in task_files.items():
        text = (ROOT / path).read_text()
        assert "ubuntu_version" in text, f"{provider} does not select by ubuntu_version"


def test_input_rejects_unknown_or_provider_unverified_versions_before_provisioning():
    text = (ROOT / "input.yml").read_text()
    assert "supported_ubuntu_versions" in text
    assert "cloud_provider_ubuntu_versions" in text
    assert "Ubuntu {{ ubuntu_version }} image selection is not verified" in text
    assert "Amazon Lightsail (unsupported/unverified)" in text
    assert "Microsoft Azure (unsupported/unverified)" in text


def test_local_deployment_ci_covers_both_supported_releases():
    workflow = yaml.safe_load((ROOT / ".github/workflows/integration-tests.yml").read_text())
    job = workflow["jobs"]["localhost-deployment"]
    assert job["strategy"]["matrix"]["os"] == ["ubuntu-22.04", "ubuntu-24.04"]
    assert job["runs-on"] == "${{ matrix.os }}"


def test_support_documentation_marks_live_provider_verification_status():
    docs = (ROOT / "docs/deploy-to-ubuntu.md").read_text()
    assert "Provider image selector status" in docs
    assert "No live provider deployment was performed" in docs
    for provider in ("Azure", "Lightsail", "OpenStack", "CloudStack"):
        assert provider in docs
