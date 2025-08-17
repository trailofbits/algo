#!/usr/bin/env python3
"""
Test that Ansible templates render correctly
This catches undefined variables, syntax errors, and logic bugs
"""

import os
import sys
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined, TemplateSyntaxError, UndefinedError

# Add parent directory to path for fixtures
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fixtures import load_test_variables


# Mock Ansible filters that don't exist in plain Jinja2
def mock_to_uuid(value):
    """Mock the to_uuid filter"""
    return "12345678-1234-5678-1234-567812345678"


def mock_bool(value):
    """Mock the bool filter"""
    return str(value).lower() in ("true", "1", "yes", "on")


def mock_lookup(type, path):
    """Mock the lookup function"""
    # Return fake data for file lookups
    if type == "file":
        if "private" in path:
            return "MOCK_PRIVATE_KEY_BASE64=="
        elif "public" in path:
            return "MOCK_PUBLIC_KEY_BASE64=="
        elif "preshared" in path:
            return "MOCK_PRESHARED_KEY_BASE64=="
    return "MOCK_LOOKUP_DATA"


def get_test_variables():
    """Get a comprehensive set of test variables for template rendering"""
    # Load from fixtures for consistency
    return load_test_variables()


def find_templates():
    """Find all Jinja2 template files in the repo"""
    templates = []
    for pattern in ["**/*.j2", "**/*.jinja2", "**/*.yml.j2"]:
        templates.extend(Path(".").glob(pattern))
    return templates


def test_template_syntax():
    """Test that all templates have valid Jinja2 syntax"""
    templates = find_templates()

    # Skip some paths that aren't real templates
    skip_paths = [".git/", "venv/", ".venv/", ".env/", "configs/"]

    # Skip templates that use Ansible-specific filters
    skip_templates = ["vpn-dict.j2", "mobileconfig.j2", "dnscrypt-proxy.toml.j2"]

    errors = []
    skipped = 0
    for template_path in templates:
        # Skip unwanted paths
        if any(skip in str(template_path) for skip in skip_paths):
            continue

        # Skip templates with Ansible-specific features
        if any(skip in str(template_path) for skip in skip_templates):
            skipped += 1
            continue

        try:
            template_dir = template_path.parent
            env = Environment(loader=FileSystemLoader(template_dir), undefined=StrictUndefined)

            # Just try to load the template - this checks syntax
            env.get_template(template_path.name)

        except TemplateSyntaxError as e:
            errors.append(f"{template_path}: Syntax error - {e}")
        except Exception as e:
            errors.append(f"{template_path}: Error loading - {e}")

    if errors:
        print(f"✗ Template syntax check failed with {len(errors)} errors:")
        for error in errors[:10]:  # Show first 10 errors
            print(f"  - {error}")
        if len(errors) > 10:
            print(f"  ... and {len(errors) - 10} more")
        assert False, "Template syntax errors found"
    else:
        print(f"✓ Template syntax check passed ({len(templates) - skipped} templates, {skipped} skipped)")


def test_critical_templates():
    """Test that critical templates render with test data"""
    critical_templates = [
        "roles/wireguard/templates/client.conf.j2",
        "roles/strongswan/templates/ipsec.conf.j2",
        "roles/strongswan/templates/ipsec.secrets.j2",
        "roles/dns/templates/adblock.sh.j2",
        "roles/dns/templates/dnsmasq.conf.j2",
        "roles/common/templates/rules.v4.j2",
        "roles/common/templates/rules.v6.j2",
    ]

    test_vars = get_test_variables()
    errors = []

    for template_path in critical_templates:
        if not os.path.exists(template_path):
            continue  # Skip if template doesn't exist

        try:
            template_dir = os.path.dirname(template_path)
            template_name = os.path.basename(template_path)

            env = Environment(loader=FileSystemLoader(template_dir), undefined=StrictUndefined)

            # Add mock functions
            env.globals["lookup"] = mock_lookup
            env.filters["to_uuid"] = mock_to_uuid
            env.filters["bool"] = mock_bool

            template = env.get_template(template_name)

            # Add item context for templates that use loops
            if "client" in template_name:
                test_vars["item"] = ("test-user", "test-user")

            # Try to render
            output = template.render(**test_vars)

            # Basic validation - should produce some output
            assert len(output) > 0, f"Empty output from {template_path}"

        except UndefinedError as e:
            errors.append(f"{template_path}: Missing variable - {e}")
        except Exception as e:
            errors.append(f"{template_path}: Render error - {e}")

    if errors:
        print("✗ Critical template rendering failed:")
        for error in errors:
            print(f"  - {error}")
        assert False, "Critical template rendering errors"
    else:
        print("✓ Critical template rendering test passed")


def test_variable_consistency():
    """Check that commonly used variables are defined consistently"""
    # Variables that should be used consistently across templates
    common_vars = [
        "server_name",
        "IP_subject_alt_name",
        "wireguard_port",
        "wireguard_network",
        "dns_servers",
        "users",
    ]

    # Check if main.yml defines these
    if os.path.exists("main.yml"):
        with open("main.yml") as f:
            content = f.read()

        missing = []
        for var in common_vars:
            # Simple check - could be improved
            if var not in content:
                missing.append(var)

        if missing:
            print(f"⚠ Variables possibly not defined in main.yml: {missing}")

    print("✓ Variable consistency check completed")


def test_wireguard_ipv6_endpoints():
    """Test that WireGuard client configs properly format IPv6 endpoints"""
    test_cases = [
        # IPv4 address - should not be bracketed
        {"IP_subject_alt_name": "192.168.1.100", "expected_endpoint": "Endpoint = 192.168.1.100:51820"},
        # IPv6 address - should be bracketed
        {
            "IP_subject_alt_name": "2600:3c01::f03c:91ff:fedf:3b2a",
            "expected_endpoint": "Endpoint = [2600:3c01::f03c:91ff:fedf:3b2a]:51820",
        },
        # Hostname - should not be bracketed
        {"IP_subject_alt_name": "vpn.example.com", "expected_endpoint": "Endpoint = vpn.example.com:51820"},
        # IPv6 with zone ID - should be bracketed
        {"IP_subject_alt_name": "fe80::1%eth0", "expected_endpoint": "Endpoint = [fe80::1%eth0]:51820"},
    ]

    template_path = "roles/wireguard/templates/client.conf.j2"
    if not os.path.exists(template_path):
        print(f"⚠ Skipping IPv6 endpoint test - {template_path} not found")
        return

    base_vars = get_test_variables()
    errors = []

    for test_case in test_cases:
        try:
            # Set up test variables
            test_vars = {**base_vars, **test_case}
            test_vars["item"] = ("test-user", "test-user")

            # Render template
            env = Environment(loader=FileSystemLoader("roles/wireguard/templates"), undefined=StrictUndefined)
            env.globals["lookup"] = mock_lookup

            template = env.get_template("client.conf.j2")
            output = template.render(**test_vars)

            # Check if the expected endpoint format is in the output
            if test_case["expected_endpoint"] not in output:
                errors.append(
                    f"Expected '{test_case['expected_endpoint']}' for IP '{test_case['IP_subject_alt_name']}' but not found in output"
                )
                # Print relevant part of output for debugging
                for line in output.split("\n"):
                    if "Endpoint" in line:
                        errors.append(f"  Found: {line.strip()}")

        except Exception as e:
            errors.append(f"Error testing {test_case['IP_subject_alt_name']}: {e}")

    if errors:
        print("✗ WireGuard IPv6 endpoint test failed:")
        for error in errors:
            print(f"  - {error}")
        assert False, "IPv6 endpoint formatting errors"
    else:
        print("✓ WireGuard IPv6 endpoint test passed (4 test cases)")


def test_template_conditionals():
    """Test templates with different conditional states"""
    test_cases = [
        # WireGuard enabled, IPsec disabled
        {
            "wireguard_enabled": True,
            "ipsec_enabled": False,
            "dns_encryption": True,
            "dns_adblocking": True,
            "algo_ssh_tunneling": False,
        },
        # IPsec enabled, WireGuard disabled
        {
            "wireguard_enabled": False,
            "ipsec_enabled": True,
            "dns_encryption": False,
            "dns_adblocking": False,
            "algo_ssh_tunneling": True,
        },
        # Both enabled
        {
            "wireguard_enabled": True,
            "ipsec_enabled": True,
            "dns_encryption": True,
            "dns_adblocking": True,
            "algo_ssh_tunneling": True,
        },
    ]

    base_vars = get_test_variables()

    for i, test_case in enumerate(test_cases):
        # Merge test case with base vars
        test_vars = {**base_vars, **test_case}

        # Test a few templates that have conditionals
        conditional_templates = [
            "roles/common/templates/rules.v4.j2",
        ]

        for template_path in conditional_templates:
            if not os.path.exists(template_path):
                continue

            try:
                template_dir = os.path.dirname(template_path)
                template_name = os.path.basename(template_path)

                env = Environment(loader=FileSystemLoader(template_dir), undefined=StrictUndefined)

                # Add mock functions
                env.globals["lookup"] = mock_lookup
                env.filters["to_uuid"] = mock_to_uuid
                env.filters["bool"] = mock_bool

                template = env.get_template(template_name)
                output = template.render(**test_vars)

                # Verify conditionals work
                if test_case.get("wireguard_enabled"):
                    assert str(test_vars["wireguard_port"]) in output, f"WireGuard port missing when enabled (case {i})"

            except Exception as e:
                print(f"✗ Conditional test failed for {template_path} case {i}: {e}")
                raise

    print("✓ Template conditional tests passed")


if __name__ == "__main__":
    # Check if we have Jinja2 available
    try:
        import jinja2  # noqa: F401
    except ImportError:
        print("⚠ Skipping template tests - jinja2 not installed")
        print("  Run: pip install jinja2")
        sys.exit(0)

    tests = [
        test_template_syntax,
        test_critical_templates,
        test_variable_consistency,
        test_wireguard_ipv6_endpoints,
        test_template_conditionals,
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
        print(f"\nAll {len(tests)} template tests passed!")
