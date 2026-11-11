#!/usr/bin/env python3
"""
Enhanced tests for StrongSwan templates.
Tests all strongswan role templates with various configurations.
"""

import os
import sys
import uuid

from jinja2 import Environment, FileSystemLoader, StrictUndefined

# Add parent directory to path for fixtures
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fixtures import load_test_variables


def mock_to_uuid(value):
    """Mock the to_uuid filter"""
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, str(value)))


def mock_bool(value):
    """Mock the bool filter"""
    return str(value).lower() in ("true", "1", "yes", "on")


def mock_version(version_string, comparison):
    """Mock the version comparison filter"""
    # Simple mock - just return True for now
    return True


def mock_b64encode(value):
    """Mock base64 encoding"""
    import base64

    if isinstance(value, str):
        value = value.encode("utf-8")
    return base64.b64encode(value).decode("ascii")


def mock_b64decode(value):
    """Mock base64 decoding"""
    import base64

    return base64.b64decode(value).decode("utf-8")


def get_strongswan_test_variables(scenario="default"):
    """Get test variables for StrongSwan templates with different scenarios."""
    base_vars = load_test_variables()

    # Add StrongSwan specific variables
    strongswan_vars = {
        "ipsec_config_path": "/etc/ipsec.d",
        "ipsec_pki_path": "/etc/ipsec.d",
        "strongswan_enabled": True,
        "strongswan_network": "10.19.48.0/24",
        "strongswan_network_ipv6": "fd9d:bc11:4021::/64",
        "strongswan_log_level": "2",
        "openssl_constraint_random_id": "test-" + str(uuid.uuid4()),
        "subjectAltName": "IP:10.0.0.1,IP:2600:3c01::f03c:91ff:fedf:3b2a",
        "subjectAltName_type": "IP",
        "subjectAltName_client": "IP:10.0.0.1",
        "ansible_default_ipv6": {"address": "2600:3c01::f03c:91ff:fedf:3b2a"},
        "openssl_version": "3.0.0",
        "p12_export_password": "test-password",
        "ike_lifetime": "24h",
        "ipsec_lifetime": "8h",
        "ike_dpd": "30s",
        "ipsec_dead_peer_detection": True,
        "rekey_margin": "3m",
        "rekeymargin": "3m",
        "dpddelay": "35s",
        "keyexchange": "ikev2",
        "ike_cipher": "aes128gcm16-prfsha512-ecp256",
        "esp_cipher": "aes128gcm16-ecp256",
        "leftsourceip": "10.19.48.1",
        "leftsubnet": "0.0.0.0/0,::/0",
        "rightsourceip": "10.19.48.2/24,fd9d:bc11:4021::2/64",
    }

    # Merge with base variables
    test_vars = {**base_vars, **strongswan_vars}

    # Apply scenario-specific overrides
    if scenario == "ipv4_only":
        test_vars["ipv6_support"] = False
        test_vars["subjectAltName"] = "IP:10.0.0.1"
        test_vars["ansible_default_ipv6"] = None
    elif scenario == "dns_hostname":
        test_vars["IP_subject_alt_name"] = "vpn.example.com"
        test_vars["subjectAltName"] = "DNS:vpn.example.com"
        test_vars["subjectAltName_type"] = "DNS"
    elif scenario == "openssl_legacy":
        test_vars["openssl_version"] = "1.1.1"

    return test_vars


def test_strongswan_templates():
    """Test all StrongSwan templates with various configurations."""
    templates = [
        "roles/strongswan/templates/ipsec.conf.j2",
        "roles/strongswan/templates/ipsec.secrets.j2",
        "roles/strongswan/templates/strongswan.conf.j2",
        "roles/strongswan/templates/charon.conf.j2",
        "roles/strongswan/templates/client_ipsec.conf.j2",
        "roles/strongswan/templates/client_ipsec.secrets.j2",
        "roles/strongswan/templates/100-CustomLimitations.conf.j2",
    ]

    scenarios = ["default", "ipv4_only", "dns_hostname", "openssl_legacy"]
    errors = []
    tested = 0

    for template_path in templates:
        assert os.path.exists(template_path), f"Template not found: {template_path}"

        template_dir = os.path.dirname(template_path)
        template_name = os.path.basename(template_path)

        for scenario in scenarios:
            tested += 1
            test_vars = get_strongswan_test_variables(scenario)

            try:
                env = Environment(loader=FileSystemLoader(template_dir), undefined=StrictUndefined)

                # Add mock filters
                env.filters["to_uuid"] = mock_to_uuid
                env.filters["bool"] = mock_bool
                env.filters["b64encode"] = mock_b64encode
                env.filters["b64decode"] = mock_b64decode
                env.tests["version"] = mock_version

                # For client templates, add item context
                if "client" in template_name:
                    test_vars["item"] = "testuser"

                template = env.get_template(template_name)
                output = template.render(**test_vars)

                # Basic validation
                assert len(output) > 0, f"Empty output from {template_path} ({scenario})"

                # Specific validations based on template
                if "ipsec.conf" in template_name and "client" not in template_name:
                    assert "conn" in output, "Missing connection definition"
                    if scenario != "ipv4_only" and test_vars.get("ipv6_support"):
                        assert "::/0" in output or "fd9d:bc11" in output, "Missing IPv6 configuration"

                if "ipsec.secrets" in template_name:
                    assert "PSK" in output or "ECDSA" in output, "Missing authentication method"

                if "strongswan.conf" in template_name:
                    assert "charon" in output, "Missing charon configuration"

                print(f"  ✅ {template_name} ({scenario})")

            except Exception as e:
                errors.append(f"{template_path} ({scenario}): {e!s}")
                print(f"  ❌ {template_name} ({scenario}): {e!s}")

    if errors:
        print(f"\n❌ StrongSwan template tests failed with {len(errors)} errors")
        for error in errors[:5]:
            print(f"    {error}")
    assert not errors, f"StrongSwan template rendering failed: {errors}"
    print(f"\n✅ All StrongSwan template tests passed ({tested} tests)")


def test_openssl_template_constraints():
    """Test the OpenSSL task template that had the inline comment issue."""
    # This tests the actual openssl.yml task file to ensure our fix works
    import yaml

    openssl_path = "roles/strongswan/tasks/openssl.yml"
    assert os.path.exists(openssl_path), "OpenSSL tasks file not found"

    try:
        with open(openssl_path) as f:
            content = yaml.safe_load(f)

        # Find the CA CSR task
        ca_csr_task = None
        for task in content:
            if isinstance(task, dict) and task.get("name", "").startswith("Create certificate signing request"):
                ca_csr_task = task
                break

        if ca_csr_task:
            # Check that name_constraints_permitted is properly formatted
            csr_module = ca_csr_task.get("community.crypto.openssl_csr_pipe", {})
            constraints = csr_module.get("name_constraints_permitted", "")

            # The constraints should be a Jinja2 template without inline comments
            if "#" in str(constraints):
                # Check if the # is within {{ }}
                import re

                jinja_blocks = re.findall(r"\{\{.*?\}\}", str(constraints), re.DOTALL)
                for block in jinja_blocks:
                    if "#" in block:
                        raise AssertionError("Found inline comment in Jinja2 expression")

        print("✅ OpenSSL template constraints validated")

    except Exception as e:
        raise AssertionError(f"Error checking OpenSSL tasks: {e}") from e


if __name__ == "__main__":
    print("🔍 Testing StrongSwan templates...\n")

    tests = [
        test_strongswan_templates,
        test_openssl_template_constraints,
    ]

    for test in tests:
        test()

    print("\n✅ All StrongSwan template tests passed!")
