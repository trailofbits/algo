#!/usr/bin/env python3
"""
Test cloud provider instance type configurations.

Validates config.cfg against known-deprecated instance types that will fail
at deployment time. Based on issue #14730 (Hetzner cx->cpx migration).

Why not regex format validation? Providers constantly add new instance families
(AWS m7.*, g5.*, etc.). Regex patterns would break on legitimate new values.
Instead, we only check for KNOWN-BAD values that are definitively deprecated.
"""

from pathlib import Path

import yaml

# Only values that are KNOWN to fail - update when providers deprecate more
DEPRECATED_VALUES = {
    # Intel CX series removed Sept 2024 - AMD CPX series still available
    # https://docs.hetzner.com/cloud/servers/deprecated-plans/
    "hetzner": {"server_type": ["cx11", "cx21", "cx31", "cx41", "cx51"]},
    # Old naming scheme deprecated ~2018, use s-*vcpu-* format
    "digitalocean": {"size": ["512mb", "1gb", "2gb", "4gb", "8gb", "16gb"]},
    # Previous gen, unavailable in VPC after EC2-Classic retirement
    # https://aws.amazon.com/ec2/previous-generation/
    "ec2": {"size": ["t1.micro", "m1.small", "m1.medium", "m1.large"]},
}

REQUIRED_FIELDS = {
    "ec2": ["size"],
    "digitalocean": ["size", "image"],
    "hetzner": ["server_type", "image"],
    "vultr": ["size", "os"],
    "linode": ["type", "image"],
    "gce": ["size", "image"],
    "azure": ["size"],
    "lightsail": ["size", "image"],
    "scaleway": ["size", "image"],
}


def load_config():
    """Load config.cfg from the repository root."""
    config_path = Path(__file__).parents[2] / "config.cfg"
    return yaml.safe_load(config_path.read_text())


def test_no_deprecated_instance_types():
    """Catch deprecated instance types before deployment fails."""
    providers = load_config().get("cloud_providers", {})

    for provider, fields in DEPRECATED_VALUES.items():
        if provider not in providers:
            continue
        for field, deprecated in fields.items():
            value = providers[provider].get(field)
            assert value not in deprecated, f"{provider}.{field}='{value}' is deprecated and will fail"


def test_required_fields_present():
    """Ensure critical fields aren't empty."""
    providers = load_config().get("cloud_providers", {})

    for provider, fields in REQUIRED_FIELDS.items():
        if provider not in providers:
            continue
        for field in fields:
            value = providers[provider].get(field)
            # Skip nested dicts (like ec2.image which has subfields)
            if isinstance(value, dict):
                continue
            assert value, f"{provider}.{field} is empty or missing"


def test_no_malformed_values():
    """Basic sanity - no control chars, reasonable length."""
    providers = load_config().get("cloud_providers", {})

    for provider, settings in providers.items():
        if not isinstance(settings, dict):
            continue
        for field, value in settings.items():
            if not isinstance(value, str):
                continue
            assert "\n" not in value, f"{provider}.{field} contains newline"
            assert len(value) <= 128, f"{provider}.{field} too long ({len(value)} chars)"
