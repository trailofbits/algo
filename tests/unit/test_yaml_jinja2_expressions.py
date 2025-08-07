#!/usr/bin/env python3
"""
Test that Jinja2 expressions within YAML files are valid.
This catches issues like inline comments in Jinja2 expressions within YAML task files.
"""

import re
from pathlib import Path

import pytest
import yaml
from jinja2 import Environment, StrictUndefined, TemplateSyntaxError


def find_yaml_files_with_jinja2():
    """Find all YAML files that might contain Jinja2 expressions."""
    yaml_files = []

    # Look for YAML files in roles that are likely to have Jinja2
    patterns = ["roles/**/tasks/*.yml", "roles/**/defaults/*.yml", "roles/**/vars/*.yml", "playbooks/*.yml", "*.yml"]

    skip_dirs = {".git", ".venv", "venv", ".env", "configs"}

    for pattern in patterns:
        for path in Path(".").glob(pattern):
            if not any(skip_dir in path.parts for skip_dir in skip_dirs):
                yaml_files.append(path)

    return sorted(yaml_files)


def extract_jinja2_expressions(content):
    """Extract all Jinja2 expressions from text content."""
    expressions = []

    # Find {{ ... }} expressions (variable interpolations)
    for match in re.finditer(r"\{\{(.+?)\}\}", content, re.DOTALL):
        expressions.append(
            {
                "type": "variable",
                "content": match.group(1),
                "full": match.group(0),
                "start": match.start(),
                "end": match.end(),
            }
        )

    # Find {% ... %} expressions (control structures)
    for match in re.finditer(r"\{%(.+?)%\}", content, re.DOTALL):
        expressions.append(
            {
                "type": "control",
                "content": match.group(1),
                "full": match.group(0),
                "start": match.start(),
                "end": match.end(),
            }
        )

    return expressions


def find_line_number(content, position):
    """Find the line number for a given position in content."""
    return content[:position].count("\n") + 1


def validate_jinja2_expression(expression, context_vars=None):
    """
    Validate a single Jinja2 expression.
    Returns (is_valid, error_message)
    """
    if context_vars is None:
        context_vars = get_test_variables()

    # First check for inline comments - this is the main issue we want to catch
    if "#" in expression["content"]:
        # Check if the # is within a list or dict literal
        content = expression["content"]
        # Remove strings to avoid false positives
        cleaned = re.sub(r'"[^"]*"', '""', content)
        cleaned = re.sub(r"'[^']*'", "''", cleaned)

        # Look for # that appears to be a comment
        # The # should have something before it (not at start) and something after (the comment text)
        # Also check for # at the start of a line within the expression
        if "#" in cleaned:
            # Check each line in the cleaned expression
            for line in cleaned.split("\n"):
                line = line.strip()
                if "#" in line:
                    # If # appears and it's not escaped (\#)
                    hash_idx = line.find("#")
                    if hash_idx >= 0:
                        # Check if it's escaped
                        if hash_idx == 0 or line[hash_idx - 1] != "\\":
                            # This looks like an inline comment
                            return (
                                False,
                                "Inline comment (#) found in Jinja2 expression - comments must be outside expressions",
                            )

    try:
        env = Environment(undefined=StrictUndefined)

        # Add common Ansible filters (expanded list)
        env.filters["bool"] = lambda x: bool(x)
        env.filters["default"] = lambda x, d="": x if x else d
        env.filters["to_uuid"] = lambda x: "mock-uuid"
        env.filters["b64encode"] = lambda x: "mock-base64"
        env.filters["b64decode"] = lambda x: "mock-decoded"
        env.filters["version"] = lambda x, op: True
        env.filters["ternary"] = lambda x, y, z=None: y if x else (z if z is not None else "")
        env.filters["regex_replace"] = lambda x, p, r: x
        env.filters["difference"] = lambda x, y: list(set(x) - set(y))
        env.filters["strftime"] = lambda fmt, ts: "mock-timestamp"
        env.filters["int"] = lambda x: int(x) if x else 0
        env.filters["list"] = lambda x: list(x)
        env.filters["map"] = lambda x, *args: x
        env.tests["version"] = lambda x, op: True

        # Wrap the expression in appropriate delimiters for parsing
        if expression["type"] == "variable":
            template_str = "{{" + expression["content"] + "}}"
        else:
            template_str = "{%" + expression["content"] + "%}"

        # Try to compile the template
        template = env.from_string(template_str)

        # Try to render it with test variables
        # This will catch undefined variables and runtime errors
        template.render(**context_vars)

        return True, None

    except TemplateSyntaxError as e:
        # Check for the specific inline comment issue
        if "#" in expression["content"]:
            # Check if the # is within a list or dict literal
            content = expression["content"]
            # Remove strings to avoid false positives
            cleaned = re.sub(r'"[^"]*"', '""', content)
            cleaned = re.sub(r"'[^']*'", "''", cleaned)

            # Look for # that appears to be a comment (not in string, not escaped)
            if re.search(r"[^\\\n]#[^\}]", cleaned):
                return False, "Inline comment (#) found in Jinja2 expression - comments must be outside expressions"

        return False, f"Syntax error: {e.message}"

    except Exception as e:
        # Be lenient - we mainly care about inline comments and basic syntax
        # Ignore runtime errors (undefined vars, missing attributes, etc.)
        error_str = str(e).lower()
        if any(ignore in error_str for ignore in ["undefined", "has no attribute", "no filter"]):
            return True, None  # These are runtime issues, not syntax issues
        return False, f"Error: {str(e)}"


def get_test_variables():
    """Get a comprehensive set of test variables for expression validation."""
    return {
        # Network configuration
        "IP_subject_alt_name": "10.0.0.1",
        "server_name": "algo-vpn",
        "wireguard_port": 51820,
        "wireguard_network": "10.19.49.0/24",
        "wireguard_network_ipv6": "fd9d:bc11:4021::/64",
        "strongswan_network": "10.19.48.0/24",
        "strongswan_network_ipv6": "fd9d:bc11:4020::/64",
        # Feature flags
        "ipv6_support": True,
        "dns_encryption": True,
        "dns_adblocking": True,
        "wireguard_enabled": True,
        "ipsec_enabled": True,
        # OpenSSL/PKI
        "openssl_constraint_random_id": "test-uuid-12345",
        "CA_password": "test-password",
        "p12_export_password": "test-p12-password",
        "ipsec_pki_path": "/etc/ipsec.d",
        "ipsec_config_path": "/etc/ipsec.d",
        "subjectAltName": "IP:10.0.0.1,DNS:vpn.example.com",
        "subjectAltName_type": "IP",
        # Ansible variables
        "ansible_default_ipv4": {"address": "10.0.0.1"},
        "ansible_default_ipv6": {"address": "2600:3c01::f03c:91ff:fedf:3b2a"},
        "ansible_distribution": "Ubuntu",
        "ansible_distribution_version": "22.04",
        "ansible_date_time": {"epoch": "1234567890"},
        # User management
        "users": ["alice", "bob", "charlie"],
        "all_users": ["alice", "bob", "charlie", "david"],
        # Common variables
        "item": "test-item",
        "algo_provider": "local",
        "algo_server_name": "algo-vpn",
        "dns_servers": ["1.1.1.1", "1.0.0.1"],
        # OpenSSL version for conditionals
        "openssl_version": "3.0.0",
        # IPsec configuration
        "certificate_validity_days": 3650,
        "ike_cipher": "aes128gcm16-prfsha512-ecp256",
        "esp_cipher": "aes128gcm16-ecp256",
    }


def validate_yaml_file(yaml_path, check_inline_comments_only=False):
    """
    Validate all Jinja2 expressions in a YAML file.
    Returns (has_inline_comments, list_of_inline_comment_errors, list_of_other_errors)
    """
    inline_comment_errors = []
    other_errors = []

    try:
        with open(yaml_path) as f:
            content = f.read()

        # First, check if it's valid YAML
        try:
            yaml.safe_load(content)
        except yaml.YAMLError:
            # YAML syntax error, not our concern here
            return False, [], []

        # Extract all Jinja2 expressions
        expressions = extract_jinja2_expressions(content)

        if not expressions:
            return False, [], []  # No Jinja2 expressions to validate

        # Validate each expression
        for expr in expressions:
            is_valid, error = validate_jinja2_expression(expr)

            if not is_valid:
                line_num = find_line_number(content, expr["start"])
                error_msg = f"{yaml_path}:{line_num}: {error}"

                # Separate inline comment errors from other errors
                if error and "inline comment" in error.lower():
                    inline_comment_errors.append(error_msg)
                    # Show context for inline comment errors
                    if len(expr["full"]) < 200:
                        inline_comment_errors.append(f"  Expression: {expr['full'][:100]}...")
                elif not check_inline_comments_only:
                    other_errors.append(error_msg)

    except Exception as e:
        if not check_inline_comments_only:
            other_errors.append(f"{yaml_path}: Error reading file: {e}")

    return len(inline_comment_errors) > 0, inline_comment_errors, other_errors


def test_regression_openssl_inline_comments():
    """
    Regression test for the specific OpenSSL inline comment bug that was reported.
    Tests that we correctly detect inline comments in the exact pattern that caused the issue.
    """
    # The problematic expression that was reported
    problematic_expr = """{{ [
  subjectAltName_type + ':' + IP_subject_alt_name + ('/255.255.255.255' if subjectAltName_type == 'IP' else ''),
  'DNS:' + openssl_constraint_random_id,        # Per-deployment UUID prevents cross-deployment reuse
  'email:' + openssl_constraint_random_id       # Unique email domain isolates certificate scope
] + (
  ['IP:' + ansible_default_ipv6['address'] + '/128'] if ipv6_support else []
) }}"""

    # The fixed expression (without inline comments)
    fixed_expr = """{{ [
  subjectAltName_type + ':' + IP_subject_alt_name + ('/255.255.255.255' if subjectAltName_type == 'IP' else ''),
  'DNS:' + openssl_constraint_random_id,
  'email:' + openssl_constraint_random_id
] + (
  ['IP:' + ansible_default_ipv6['address'] + '/128'] if ipv6_support else []
) }}"""

    # Test the problematic expression - should fail
    expr_with_comments = {
        "type": "variable",
        "content": problematic_expr[2:-2],  # Remove {{ }}
        "full": problematic_expr,
    }
    is_valid, error = validate_jinja2_expression(expr_with_comments)
    assert not is_valid, "Should have detected inline comments in problematic expression"
    assert "inline comment" in error.lower(), f"Expected inline comment error, got: {error}"

    # Test the fixed expression - should pass
    expr_fixed = {
        "type": "variable",
        "content": fixed_expr[2:-2],  # Remove {{ }}
        "full": fixed_expr,
    }
    is_valid, error = validate_jinja2_expression(expr_fixed)
    assert is_valid, f"Fixed expression should pass but got error: {error}"


def test_edge_cases_inline_comments():
    """
    Test various edge cases for inline comment detection.
    Ensures we correctly handle hashes in strings, escaped hashes, and various comment patterns.
    """
    test_cases = [
        # (expression, should_pass, description)
        ("{{ 'string with # hash' }}", True, "Hash in string should pass"),
        ('{{ "another # in string" }}', True, "Hash in double-quoted string should pass"),
        ("{{ var # comment }}", False, "Simple inline comment should fail"),
        ("{{ var1 + var2  # This is an inline comment }}", False, "Inline comment with text should fail"),
        (r"{{ '\#' + 'escaped hash' }}", True, "Escaped hash should pass"),
        ("{% if true # comment %}", False, "Comment in control block should fail"),
        ("{% for item in list # loop comment %}", False, "Comment in for loop should fail"),
        ("{{ {'key': 'value # not a comment'} }}", True, "Hash in dict string value should pass"),
        ("{{ url + '/#anchor' }}", True, "URL fragment should pass"),
        ("{{ '#FF0000' }}", True, "Hex color code should pass"),
        ("{{ var }}  # comment outside", True, "Comment outside expression should pass"),
        (
            """{{ [
            'item1',  # comment here
            'item2'
        ] }}""",
            False,
            "Multi-line with inline comment should fail",
        ),
    ]

    for expr_str, should_pass, description in test_cases:
        # For the "comment outside" case, extract just the Jinja2 expression
        if "{{" in expr_str and "#" in expr_str and expr_str.index("#") > expr_str.index("}}"):
            # Comment is outside the expression - extract just the expression part
            match = re.search(r"(\{\{.+?\}\})", expr_str)
            if match:
                actual_expr = match.group(1)
                expr_type = "variable"
                content = actual_expr[2:-2].strip()
            else:
                continue
        elif expr_str.strip().startswith("{{"):
            expr_type = "variable"
            content = expr_str.strip()[2:-2]
            actual_expr = expr_str.strip()
        elif expr_str.strip().startswith("{%"):
            expr_type = "control"
            content = expr_str.strip()[2:-2]
            actual_expr = expr_str.strip()
        else:
            continue

        expr = {"type": expr_type, "content": content, "full": actual_expr}

        is_valid, error = validate_jinja2_expression(expr)

        if should_pass:
            assert is_valid, f"{description}: {error}"
        else:
            assert not is_valid, f"{description}: Should have failed but passed"
            assert "inline comment" in (error or "").lower(), (
                f"{description}: Expected inline comment error, got: {error}"
            )


def test_yaml_files_no_inline_comments():
    """
    Test that all YAML files in the project don't contain inline comments in Jinja2 expressions.
    """
    yaml_files = find_yaml_files_with_jinja2()

    all_inline_comment_errors = []
    files_with_inline_comments = []

    for yaml_file in yaml_files:
        has_inline_comments, inline_errors, _ = validate_yaml_file(yaml_file, check_inline_comments_only=True)

        if has_inline_comments:
            files_with_inline_comments.append(str(yaml_file))
            all_inline_comment_errors.extend(inline_errors)

    # Assert no inline comments found
    assert not all_inline_comment_errors, (
        f"Found inline comments in {len(files_with_inline_comments)} files:\n"
        + "\n".join(all_inline_comment_errors[:10])  # Show first 10 errors
    )


def test_openssl_file_specifically():
    """
    Specifically test the OpenSSL file that had the original bug.
    """
    openssl_file = Path("roles/strongswan/tasks/openssl.yml")

    if not openssl_file.exists():
        pytest.skip(f"{openssl_file} not found")

    has_inline_comments, inline_errors, _ = validate_yaml_file(openssl_file)

    assert not has_inline_comments, f"Found inline comments in {openssl_file}:\n" + "\n".join(inline_errors)
