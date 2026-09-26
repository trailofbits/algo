"""Tests for the Scaleway provider fixes (Marketplace API v2 migration).

This test suite validates that:
1. Image lookup uses Marketplace API v2 (api.scaleway.com/marketplace/v2/local-images)
2. scaleway_compute uses the 'organization' parameter required by the
   vendored library module (it does not support 'project')
3. Zone/alias maps cover every offered region and are consistent
4. The cloud-init patch uses the Instance API user-data endpoint rather
   than the legacy cp-<alias>.scaleway.com hosts (which only resolve
   for par1/ams1)
5. destroy.yml maps full zone names back to legacy aliases
"""

from pathlib import Path

import yaml

ROLE_DIR = Path("roles/cloud-scaleway")


def _read(*parts: str) -> str:
    return (ROLE_DIR.joinpath(*parts)).read_text()


def test_scaleway_uses_marketplace_v2_api():
    """Image lookup must use Marketplace API v2 local-images endpoint."""
    content = _read("tasks", "main.yml")

    assert "api.scaleway.com/marketplace/v2/local-images" in content, (
        "Not using Marketplace API v2 local-images endpoint"
    )
    assert "api-marketplace.scaleway.com" not in content, (
        "Still using the retired api-marketplace.scaleway.com host"
    )
    assert "scaleway_image_info" not in content, "Still using broken scaleway_image_info module"
    assert "scaleway_organization_info" not in content, "Still using broken scaleway_organization_info module"
    assert "X-Auth-Token" in content, (
        "Marketplace API call must pass an explicit X-Auth-Token header "
        "(the uri module ignores the SCW_TOKEN environment variable)"
    )


def test_scaleway_compute_uses_organization_parameter():
    """scaleway_compute must receive 'organization', not 'project'."""
    content = _read("tasks", "main.yml")

    assert 'organization: "{{ algo_scaleway_org_id }}"' in content, (
        "scaleway_compute calls must pass organization (the vendored module has no project param)"
    )
    assert "project:" not in content, (
        "'project:' is not a valid scaleway_compute parameter in the vendored library module"
    )


def test_scaleway_zone_maps_are_consistent():
    """Every offered region must have a zone and a matching reverse alias."""
    defaults = yaml.safe_load((ROLE_DIR / "defaults" / "main.yml").read_text())

    regions = {r["alias"] for r in defaults["scaleway_regions"]}
    zone_map = defaults["scaleway_zone_map"]
    alias_map = defaults["scaleway_compute_alias_map"]

    assert regions, "scaleway_regions must not be empty"
    assert set(zone_map.keys()) == regions, "zone_map must cover exactly the offered regions"
    assert set(alias_map.values()) == regions, "alias_map must cover exactly the offered regions"
    assert set(zone_map.values()) == set(alias_map.keys()), "zone and alias names must match"
    assert zone_map == {v: k for k, v in alias_map.items()}, (
        "scaleway_zone_map and scaleway_compute_alias_map must be exact inverses"
    )


def test_scaleway_image_selection_filters():
    """Image fact must filter v2 results by arch, commercial type and image type."""
    content = _read("tasks", "main.yml")

    assert "local_images" in content, "Image lookup must read local_images from the v2 response"
    assert "selectattr('arch', 'equalto', cloud_providers.scaleway.arch)" in content, "Missing arch filter"
    assert "selectattr('compatible_commercial_types', 'contains', cloud_providers.scaleway.size)" in content, (
        "Missing commercial type filter"
    )
    assert "selectattr('type', 'equalto', 'instance_sbs')" in content, "Missing instance_sbs image type filter"


def test_scaleway_cloudinit_uses_instance_api():
    """Cloud-init patch must target the Instance API, not legacy cp- hosts."""
    tasks = yaml.safe_load(_read("tasks", "main.yml"))
    block = next(t["block"] for t in tasks if "block" in t)
    patch = next(t for t in block if t.get("name") == "Patch the cloud-init")

    url = patch["uri"]["url"]
    assert "instance/v1/zones/{{ algo_scaleway_zone }}/servers/" in url, (
        "Cloud-init patch must use the Instance API user-data endpoint (works in all zones)"
    )
    assert "user_data/cloud-init" in url, "Cloud-init patch must target the cloud-init user data key"
    assert "cp-" not in url, (
        "Legacy cp-<alias>.scaleway.com hosts only resolve for par1/ams1 and break other zones"
    )


def test_scaleway_destroy_maps_zone_to_alias():
    """destroy.yml must map full zone names to module-supported aliases."""
    content = _read("tasks", "destroy.yml")

    assert "algo_scaleway_compute_alias" in content, "destroy.yml must resolve the legacy compute alias"
    assert "scaleway_compute_alias_map | default({})" in content, (
        "destroy.yml is included without role defaults, so the alias map lookup must be guarded"
    )
    assert 'region: "{{ algo_scaleway_compute_alias }}"' in content, (
        "scaleway_compute must be called with the mapped alias, not the raw region"
    )


def test_scaleway_prompts_collect_org_id():
    """Prompts must collect organization/project ID and support env fallback."""
    content = _read("tasks", "prompts.yml")

    assert "Organization ID" in content, "Missing prompt for Scaleway Organization ID"
    assert "algo_scaleway_org_id:" in content, "Missing algo_scaleway_org_id fact definition"
    assert "SCW_DEFAULT_ORGANIZATION_ID" in content, (
        "Missing support for SCW_DEFAULT_ORGANIZATION_ID environment variable"
    )
    assert "console.scaleway.com" in content, "Missing instructions on where to find Organization ID"


def test_scaleway_config_has_valid_settings():
    """config.cfg must define scaleway size and arch used by the v2 filters."""
    content = Path("config.cfg").read_text()

    assert "scaleway:" in content, "Missing Scaleway configuration section"
    assert "DEV1-S" in content, "Missing Scaleway instance size (used by compatible_commercial_types filter)"
    assert "arch: x86_64" in content, "Missing Scaleway arch (used by the image arch filter)"
