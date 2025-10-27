#!/usr/bin/env python3
"""
Test Scaleway role fixes for issue #14846

This test validates that:
1. The Scaleway role uses the modern 'project' parameter instead of deprecated 'organization'
2. The Marketplace API is used for image lookup instead of the broken scaleway_image_info module
3. The prompts include organization/project ID collection
"""

import sys
from pathlib import Path

import yaml


def load_yaml_file(file_path):
    """Load and parse a YAML file"""
    with open(file_path) as f:
        return yaml.safe_load(f)


def test_scaleway_main_uses_project_parameter():
    """Test that main.yml uses 'project' instead of deprecated 'organization' parameter"""
    main_yml = Path("roles/cloud-scaleway/tasks/main.yml")
    assert main_yml.exists(), "Scaleway main.yml not found"

    with open(main_yml) as f:
        content = f.read()

    # Should NOT use the broken scaleway_organization_info module
    assert (
        "scaleway_organization_info" not in content
    ), "Still using broken scaleway_organization_info module (issue #14846)"

    # Should NOT use the broken scaleway_image_info module
    assert "scaleway_image_info" not in content, "Still using broken scaleway_image_info module"

    # Should use project parameter (modern approach)
    assert "project:" in content, "Missing 'project:' parameter in scaleway_compute calls"
    assert "algo_scaleway_org_id" in content, "Missing algo_scaleway_org_id variable reference"

    # Should NOT use deprecated organization parameter
    assert 'organization: "{{' not in content, "Still using deprecated 'organization' parameter"

    # Should use Marketplace API for image lookup
    assert "api-marketplace.scaleway.com" in content, "Not using Scaleway Marketplace API for image lookup"

    print("✓ Scaleway main.yml uses modern 'project' parameter")


def test_scaleway_prompts_collect_org_id():
    """Test that prompts.yml collects organization/project ID from user"""
    prompts_yml = Path("roles/cloud-scaleway/tasks/prompts.yml")
    assert prompts_yml.exists(), "Scaleway prompts.yml not found"

    with open(prompts_yml) as f:
        content = f.read()

    # Should prompt for organization ID
    assert "Organization ID" in content, "Missing prompt for Scaleway Organization ID"

    # Should set algo_scaleway_org_id fact
    assert "algo_scaleway_org_id:" in content, "Missing algo_scaleway_org_id fact definition"

    # Should support SCW_DEFAULT_ORGANIZATION_ID env var
    assert (
        "SCW_DEFAULT_ORGANIZATION_ID" in content
    ), "Missing support for SCW_DEFAULT_ORGANIZATION_ID environment variable"

    # Should mention console.scaleway.com for finding the ID
    assert "console.scaleway.com" in content, "Missing instructions on where to find Organization ID"

    print("✓ Scaleway prompts.yml collects organization/project ID")


def test_scaleway_config_has_valid_settings():
    """Test that config.cfg has valid Scaleway settings"""
    config_file = Path("config.cfg")
    assert config_file.exists(), "config.cfg not found"

    with open(config_file) as f:
        content = f.read()

    # Should have scaleway section
    assert "scaleway:" in content, "Missing Scaleway configuration section"

    # Should specify Ubuntu 22.04
    assert "Ubuntu 22.04" in content or "ubuntu" in content.lower(), "Missing Ubuntu image specification"

    print("✓ config.cfg has valid Scaleway settings")


def test_scaleway_marketplace_api_usage():
    """Test that the role correctly uses Scaleway Marketplace API"""
    main_yml = Path("roles/cloud-scaleway/tasks/main.yml")

    with open(main_yml) as f:
        content = f.read()

    # Should use uri module to fetch from Marketplace API
    assert "uri:" in content, "Not using uri module for API calls"

    # Should filter for Ubuntu 22.04 Jammy
    assert "Ubuntu" in content and "22" in content, "Not filtering for Ubuntu 22.04 image"

    # Should set scaleway_image_id variable
    assert "scaleway_image_id" in content, "Missing scaleway_image_id variable for image UUID"

    print("✓ Scaleway role uses Marketplace API correctly")


if __name__ == "__main__":
    tests = [
        test_scaleway_main_uses_project_parameter,
        test_scaleway_prompts_collect_org_id,
        test_scaleway_config_has_valid_settings,
        test_scaleway_marketplace_api_usage,
    ]

    failed = 0
    for test in tests:
        try:
            test()
        except AssertionError as e:
            print(f"✗ {test.__name__} failed: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ {test.__name__} error: {e}")
            failed += 1

    if failed > 0:
        print(f"\n{failed} tests failed")
        sys.exit(1)
    else:
        print(f"\nAll {len(tests)} tests passed!")
