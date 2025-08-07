#!/usr/bin/env python3
"""
Test that Jinja2 expressions within YAML files are valid.
This catches issues like inline comments in Jinja2 expressions within YAML task files.
"""
import re
import sys
from pathlib import Path

import yaml
from jinja2 import Environment, StrictUndefined, TemplateSyntaxError


def find_yaml_files_with_jinja2():
    """Find all YAML files that might contain Jinja2 expressions."""
    yaml_files = []

    # Look for YAML files in roles that are likely to have Jinja2
    patterns = [
        'roles/**/tasks/*.yml',
        'roles/**/defaults/*.yml',
        'roles/**/vars/*.yml',
        'playbooks/*.yml',
        '*.yml'
    ]

    skip_dirs = {'.git', '.venv', 'venv', '.env', 'configs'}

    for pattern in patterns:
        for path in Path('.').glob(pattern):
            if not any(skip_dir in path.parts for skip_dir in skip_dirs):
                yaml_files.append(path)

    return sorted(yaml_files)


def extract_jinja2_expressions(content):
    """Extract all Jinja2 expressions from text content."""
    expressions = []

    # Find {{ ... }} expressions (variable interpolations)
    for match in re.finditer(r'\{\{(.+?)\}\}', content, re.DOTALL):
        expressions.append({
            'type': 'variable',
            'content': match.group(1),
            'full': match.group(0),
            'start': match.start(),
            'end': match.end()
        })

    # Find {% ... %} expressions (control structures)
    for match in re.finditer(r'\{%(.+?)%\}', content, re.DOTALL):
        expressions.append({
            'type': 'control',
            'content': match.group(1),
            'full': match.group(0),
            'start': match.start(),
            'end': match.end()
        })

    return expressions


def find_line_number(content, position):
    """Find the line number for a given position in content."""
    return content[:position].count('\n') + 1


def validate_jinja2_expression(expression, context_vars=None):
    """
    Validate a single Jinja2 expression.
    Returns (is_valid, error_message)
    """
    if context_vars is None:
        context_vars = get_test_variables()

    # First check for inline comments - this is the main issue we want to catch
    if '#' in expression['content']:
        # Check if the # is within a list or dict literal
        content = expression['content']
        # Remove strings to avoid false positives
        cleaned = re.sub(r'"[^"]*"', '""', content)
        cleaned = re.sub(r"'[^']*'", "''", cleaned)

        # Look for # that appears to be a comment
        # The # should have something before it (not at start) and something after (the comment text)
        # Also check for # at the start of a line within the expression
        if '#' in cleaned:
            # Check each line in the cleaned expression
            for line in cleaned.split('\n'):
                line = line.strip()
                if '#' in line:
                    # If # appears and it's not escaped (\#)
                    hash_idx = line.find('#')
                    if hash_idx >= 0:
                        # Check if it's escaped
                        if hash_idx == 0 or line[hash_idx-1] != '\\':
                            # This looks like an inline comment
                            return False, "Inline comment (#) found in Jinja2 expression - comments must be outside expressions"

    try:
        env = Environment(undefined=StrictUndefined)

        # Add common Ansible filters (expanded list)
        env.filters['bool'] = lambda x: bool(x)
        env.filters['default'] = lambda x, d='': x if x else d
        env.filters['to_uuid'] = lambda x: 'mock-uuid'
        env.filters['b64encode'] = lambda x: 'mock-base64'
        env.filters['b64decode'] = lambda x: 'mock-decoded'
        env.filters['version'] = lambda x, op: True
        env.filters['ternary'] = lambda x, y, z=None: y if x else (z if z is not None else '')
        env.filters['regex_replace'] = lambda x, p, r: x
        env.filters['difference'] = lambda x, y: list(set(x) - set(y))
        env.filters['strftime'] = lambda fmt, ts: 'mock-timestamp'
        env.filters['int'] = lambda x: int(x) if x else 0
        env.filters['list'] = lambda x: list(x)
        env.filters['map'] = lambda x, *args: x
        env.tests['version'] = lambda x, op: True

        # Wrap the expression in appropriate delimiters for parsing
        if expression['type'] == 'variable':
            template_str = '{{' + expression['content'] + '}}'
        else:
            template_str = '{%' + expression['content'] + '%}'

        # Try to compile the template
        template = env.from_string(template_str)

        # Try to render it with test variables
        # This will catch undefined variables and runtime errors
        template.render(**context_vars)

        return True, None

    except TemplateSyntaxError as e:
        # Check for the specific inline comment issue
        if '#' in expression['content']:
            # Check if the # is within a list or dict literal
            content = expression['content']
            # Remove strings to avoid false positives
            cleaned = re.sub(r'"[^"]*"', '""', content)
            cleaned = re.sub(r"'[^']*'", "''", cleaned)

            # Look for # that appears to be a comment (not in string, not escaped)
            if re.search(r'[^\\\n]#[^\}]', cleaned):
                return False, "Inline comment (#) found in Jinja2 expression - comments must be outside expressions"

        return False, f"Syntax error: {e.message}"

    except Exception as e:
        # Be lenient - we mainly care about inline comments and basic syntax
        # Ignore runtime errors (undefined vars, missing attributes, etc.)
        error_str = str(e).lower()
        if any(ignore in error_str for ignore in ['undefined', 'has no attribute', 'no filter']):
            return True, None  # These are runtime issues, not syntax issues
        return False, f"Error: {str(e)}"


def get_test_variables():
    """Get a comprehensive set of test variables for expression validation."""
    return {
        # Network configuration
        'IP_subject_alt_name': '10.0.0.1',
        'server_name': 'algo-vpn',
        'wireguard_port': 51820,
        'wireguard_network': '10.19.49.0/24',
        'wireguard_network_ipv6': 'fd9d:bc11:4021::/64',
        'strongswan_network': '10.19.48.0/24',
        'strongswan_network_ipv6': 'fd9d:bc11:4020::/64',

        # Feature flags
        'ipv6_support': True,
        'dns_encryption': True,
        'dns_adblocking': True,
        'wireguard_enabled': True,
        'ipsec_enabled': True,

        # OpenSSL/PKI
        'openssl_constraint_random_id': 'test-uuid-12345',
        'CA_password': 'test-password',
        'p12_export_password': 'test-p12-password',
        'ipsec_pki_path': '/etc/ipsec.d',
        'ipsec_config_path': '/etc/ipsec.d',
        'subjectAltName': 'IP:10.0.0.1,DNS:vpn.example.com',
        'subjectAltName_type': 'IP',

        # Ansible variables
        'ansible_default_ipv4': {'address': '10.0.0.1'},
        'ansible_default_ipv6': {'address': '2600:3c01::f03c:91ff:fedf:3b2a'},
        'ansible_distribution': 'Ubuntu',
        'ansible_distribution_version': '22.04',
        'ansible_date_time': {'epoch': '1234567890'},

        # User management
        'users': ['alice', 'bob', 'charlie'],
        'all_users': ['alice', 'bob', 'charlie', 'david'],

        # Common variables
        'item': 'test-item',
        'algo_provider': 'local',
        'algo_server_name': 'algo-vpn',
        'dns_servers': ['1.1.1.1', '1.0.0.1'],

        # OpenSSL version for conditionals
        'openssl_version': '3.0.0',

        # IPsec configuration
        'certificate_validity_days': 3650,
        'ike_cipher': 'aes128gcm16-prfsha512-ecp256',
        'esp_cipher': 'aes128gcm16-ecp256',
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
                line_num = find_line_number(content, expr['start'])
                error_msg = f"{yaml_path}:{line_num}: {error}"

                # Separate inline comment errors from other errors
                if error and 'inline comment' in error.lower():
                    inline_comment_errors.append(error_msg)
                    # Show context for inline comment errors
                    if len(expr['full']) < 200:
                        inline_comment_errors.append(f"  Expression: {expr['full'][:100]}...")
                elif not check_inline_comments_only:
                    other_errors.append(error_msg)

    except Exception as e:
        if not check_inline_comments_only:
            other_errors.append(f"{yaml_path}: Error reading file: {e}")

    return len(inline_comment_errors) > 0, inline_comment_errors, other_errors


def test_specific_openssl_expressions():
    """
    Test the specific expressions that had the inline comment bug.
    This is a regression test for the exact issue that was reported.
    """
    print("\n🔬 Testing specific OpenSSL expressions (regression test)...")

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

    test_cases = [
        ('Problematic (with inline comments)', problematic_expr, False),
        ('Fixed (without inline comments)', fixed_expr, True),
    ]

    errors = []
    for name, expr_content, should_pass in test_cases:
        expr = {
            'type': 'variable',
            'content': expr_content[2:-2],  # Remove {{ }}
            'full': expr_content
        }

        is_valid, error = validate_jinja2_expression(expr)

        if should_pass and not is_valid:
            errors.append(f"❌ {name}: Should have passed but failed with: {error}")
        elif not should_pass and is_valid:
            errors.append(f"❌ {name}: Should have failed but passed")
        else:
            status = "✅" if should_pass else "⚠️"
            result = "passed" if is_valid else f"failed with: {error}"
            print(f"  {status} {name}: {result}")

    if errors:
        print("\n❌ Regression test FAILED:")
        for error in errors:
            print(f"    {error}")
        return False
    else:
        print("  ✅ Regression test passed - would have caught the bug!")
        return True


def main():
    """Main test function."""
    print("🔍 Validating Jinja2 expressions in YAML files for inline comments...\n")

    # First run the regression test
    regression_passed = test_specific_openssl_expressions()

    # Find all YAML files
    yaml_files = find_yaml_files_with_jinja2()
    print(f"\n📁 Found {len(yaml_files)} YAML files to check")

    all_inline_comment_errors = []
    files_with_inline_comments = []
    files_checked = 0

    # Validate each file - focus on inline comments
    for yaml_file in yaml_files:
        has_inline_comments, inline_errors, other_errors = validate_yaml_file(yaml_file, check_inline_comments_only=True)
        files_checked += 1

        if has_inline_comments:
            files_with_inline_comments.append(yaml_file)
            all_inline_comment_errors.extend(inline_errors)

    # Report results
    print(f"\n✅ Checked {files_checked} YAML files for inline comments in Jinja2 expressions")

    if all_inline_comment_errors:
        print(f"\n❌ Found inline comment issues in {len(files_with_inline_comments)} files:\n")
        # Show all inline comment errors since these are critical
        for error in all_inline_comment_errors:
            print(f"  ERROR: {error}")
    else:
        print("\n✅ No inline comments found in Jinja2 expressions!")

    # Check the specific file that had the bug
    openssl_file = Path('roles/strongswan/tasks/openssl.yml')
    if openssl_file.exists():
        print(f"\n🎯 Checking {openssl_file} specifically...")
        has_inline_comments, inline_errors, other_errors = validate_yaml_file(openssl_file)
        if not has_inline_comments:
            print(f"  ✅ {openssl_file} has no inline comments in Jinja2 expressions")
        else:
            print(f"  ❌ {openssl_file} has inline comments in Jinja2 expressions:")
            for error in inline_errors:
                print(f"    {error}")

    if all_inline_comment_errors or not regression_passed:
        print("\n❌ Found inline comment issues that need to be fixed")
        print("💡 Move comments outside of {{ }} and {% %} expressions")
        return 1
    else:
        print("\n✅ All YAML files are free of inline comments in Jinja2 expressions!")
        return 0


if __name__ == "__main__":
    sys.exit(main())
