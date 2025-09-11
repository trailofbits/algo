#!/usr/bin/env python3
"""
Comprehensive scan for any remaining string boolean issues in the codebase.
This ensures we haven't missed any other instances that could break Ansible 12.
"""

import re
from pathlib import Path


class TestComprehensiveBooleanScan:
    """Scan entire codebase for potential string boolean issues."""

    def get_yaml_files(self):
        """Get all YAML files in the project."""
        root = Path(__file__).parent.parent.parent
        yaml_files = []
        for pattern in ['**/*.yml', '**/*.yaml']:
            yaml_files.extend(root.glob(pattern))
        # Exclude test files and vendor directories
        return [f for f in yaml_files if 'test' not in str(f) and '.venv' not in str(f)]

    def test_no_string_true_false_in_set_fact(self):
        """Scan all YAML files for set_fact with string 'true'/'false'."""
        issues = []
        pattern = re.compile(r'set_fact:.*?\n.*?:\s*".*\}(true|false)\{.*"', re.MULTILINE | re.DOTALL)

        for yaml_file in self.get_yaml_files():
            with open(yaml_file) as f:
                content = f.read()

            matches = pattern.findall(content)
            if matches:
                issues.append(f"{yaml_file.name}: Found string boolean in set_fact: {matches}")

        assert not issues, "Found string booleans in set_fact:\n" + "\n".join(issues)

    def test_no_bare_false_in_jinja_else(self):
        """Check for bare 'false' after else in Jinja expressions."""
        issues = []
        # Pattern for {%- else %}false{% (should be {{ false }})
        pattern = re.compile(r'\{%-?\s*else\s*%\}(true|false)\{%')

        for yaml_file in self.get_yaml_files():
            with open(yaml_file) as f:
                content = f.read()

            matches = pattern.findall(content)
            if matches:
                issues.append(f"{yaml_file.name}: Found bare '{matches[0]}' after else")

        assert not issues, "Found bare true/false in else clauses:\n" + "\n".join(issues)

    def test_when_conditions_use_booleans(self):
        """Verify 'when:' conditions that use our variables."""
        boolean_vars = [
            'ipv6_support',
            'algo_dns_adblocking',
            'algo_ssh_tunneling',
            'algo_ondemand_cellular',
            'algo_ondemand_wifi',
            'algo_store_pki'
        ]

        potential_issues = []

        for yaml_file in self.get_yaml_files():
            with open(yaml_file) as f:
                lines = f.readlines()

            for i, line in enumerate(lines):
                if 'when:' in line:
                    for var in boolean_vars:
                        if var in line:
                            # Check if it's a simple condition (good) or comparing to string (bad)
                            if f'{var} == "true"' in line or f'{var} == "false"' in line:
                                potential_issues.append(
                                    f"{yaml_file.name}:{i+1}: Comparing {var} to string in when condition"
                                )
                            elif f'{var} != "true"' in line or f'{var} != "false"' in line:
                                potential_issues.append(
                                    f"{yaml_file.name}:{i+1}: Comparing {var} to string in when condition"
                                )

        assert not potential_issues, "Found string comparisons in when conditions:\n" + "\n".join(potential_issues)

    def test_template_files_boolean_usage(self):
        """Check Jinja2 template files for boolean usage."""
        root = Path(__file__).parent.parent.parent
        template_files = list(root.glob('**/*.j2'))

        issues = []

        for template_file in template_files:
            if '.venv' in str(template_file):
                continue

            with open(template_file) as f:
                content = f.read()

            # Check for conditionals using our boolean variables
            if 'ipv6_support' in content:
                # Look for string comparisons
                if 'ipv6_support == "true"' in content or 'ipv6_support == "false"' in content:
                    issues.append(f"{template_file.name}: Comparing ipv6_support to string")

                # Check it's used correctly in if statements
                if re.search(r'{%\s*if\s+ipv6_support\s*==\s*["\']true["\']', content):
                    issues.append(f"{template_file.name}: String comparison with ipv6_support")

        assert not issues, "Found issues in template files:\n" + "\n".join(issues)

    def test_all_when_conditions_would_work(self):
        """Test that all when: conditions in the codebase would work with boolean types."""
        root = Path(__file__).parent.parent.parent
        test_files = [
            root / "roles/common/tasks/iptables.yml",
            root / "server.yml",
            root / "users.yml",
            root / "roles/dns/tasks/main.yml"
        ]

        for test_file in test_files:
            if not test_file.exists():
                continue

            with open(test_file) as f:
                content = f.read()

            # Find all when: conditions
            when_lines = re.findall(r'when:\s*([^\n]+)', content)

            for when_line in when_lines:
                # Check if it's using one of our boolean variables
                if any(var in when_line for var in ['ipv6_support', 'algo_dns_adblocking', 'algo_ssh_tunneling']):
                    # Ensure it's not comparing to strings
                    assert '"true"' not in when_line, f"String comparison in {test_file.name}: {when_line}"
                    assert '"false"' not in when_line, f"String comparison in {test_file.name}: {when_line}"
                    assert "'true'" not in when_line, f"String comparison in {test_file.name}: {when_line}"
                    assert "'false'" not in when_line, f"String comparison in {test_file.name}: {when_line}"

    def test_no_other_problematic_patterns(self):
        """Look for other patterns that might cause boolean type issues."""
        # Patterns that could indicate boolean type issues
        problematic_patterns = [
            (r':\s*["\']true["\']$', "Assigning string 'true' to variable"),
            (r':\s*["\']false["\']$', "Assigning string 'false' to variable"),
            (r'default\(["\']true["\']\)', "Using string 'true' as default"),
            (r'default\(["\']false["\']\)', "Using string 'false' as default"),
        ]

        issues = []

        for yaml_file in self.get_yaml_files():
            with open(yaml_file) as f:
                lines = f.readlines()

            for i, line in enumerate(lines):
                for pattern, description in problematic_patterns:
                    if re.search(pattern, line):
                        # Check if it's not in a comment
                        if not line.strip().startswith('#'):
                            # Also exclude some known safe patterns
                            if 'booleans_map' not in line and 'test' not in yaml_file.name.lower():
                                issues.append(f"{yaml_file.name}:{i+1}: {description} - {line.strip()}")

        # We expect no issues with our fix
        assert not issues, "Found potential boolean type issues:\n" + "\n".join(issues[:10])  # Limit output

    def test_verify_our_fixes_are_correct(self):
        """Verify our specific fixes are in place and correct."""
        # Check facts.yml
        facts_file = Path(__file__).parent.parent.parent / "roles/common/tasks/facts.yml"
        with open(facts_file) as f:
            content = f.read()

        # Should use 'is defined', not string literals
        assert 'is defined' in content, "facts.yml should use 'is defined'"
        assert 'ipv6_support: "{% if ansible_default_ipv6[\'gateway\'] is defined %}true{% else %}false{% endif %}"' not in content, \
            "facts.yml still has the old string boolean pattern"

        # Check input.yml
        input_file = Path(__file__).parent.parent.parent / "input.yml"
        with open(input_file) as f:
            content = f.read()

        # Count occurrences of the fix
        assert content.count('{{ false }}') >= 5, "input.yml should have at least 5 instances of {{ false }}"
        assert '{%- else %}false{% endif %}' not in content, "input.yml still has bare 'false'"

    def test_templates_handle_booleans_correctly(self):
        """Test that template files handle boolean variables correctly."""
        templates_to_check = [
            ("roles/wireguard/templates/server.conf.j2", "ipv6_support"),
            ("roles/strongswan/templates/ipsec.conf.j2", "ipv6_support"),
            ("roles/dns/templates/dnscrypt-proxy.toml.j2", "ipv6_support"),
        ]

        for template_path, var_name in templates_to_check:
            template_file = Path(__file__).parent.parent.parent / template_path
            if not template_file.exists():
                continue

            with open(template_file) as f:
                content = f.read()

            if var_name in content:
                # Verify it's used in conditionals, not compared to strings
                assert f'{var_name} == "true"' not in content, \
                    f"{template_path} compares {var_name} to string 'true'"
                assert f'{var_name} == "false"' not in content, \
                    f"{template_path} compares {var_name} to string 'false'"

                # It should be used directly in if statements or with | bool filter
                if f'if {var_name}' in content or f'{var_name} |' in content:
                    pass  # Good - using it as a boolean

