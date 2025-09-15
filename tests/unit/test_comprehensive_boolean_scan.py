#!/usr/bin/env python3
"""
Test suite to prevent Ansible 12+ boolean type errors in Algo VPN codebase.

Background:
-----------
Ansible 12.0.0 introduced strict boolean type checking that breaks deployments
when string values like "true" or "false" are used in conditionals. This causes
errors like: "Conditional result (True) was derived from value of type 'str'"

What This Test Protects Against:
---------------------------------
1. String literals "true"/"false" being used instead of actual booleans
2. Bare true/false in Jinja2 else clauses (should be {{ true }}/{{ false }})
3. String comparisons in when: conditions (e.g., var == "true")
4. Variables being set to string booleans instead of actual booleans

Test Scope:
-----------
- Only tests Algo's own code (roles/, playbooks/, etc.)
- Excludes external dependencies (.env/, ansible_collections/)
- Excludes CloudFormation templates which require string booleans
- Excludes test files which may use different patterns

Mutation Testing Verified:
--------------------------
All tests have been verified to catch their target issues through mutation testing:
- Introducing bare 'false' in else clause → caught by test_no_bare_false_in_jinja_else
- Using string boolean in facts.yml → caught by test_verify_our_fixes_are_correct
- Adding string boolean assignments → caught by test_no_other_problematic_patterns

Related Issues:
---------------
- PR #14834: Fixed initial boolean type issues for Ansible 12
- Issue #14835: Fixed double-templating issues exposed by Ansible 12
"""

import re
from pathlib import Path


class TestComprehensiveBooleanScan:
    """Scan entire codebase for potential string boolean issues."""

    def get_yaml_files(self):
        """Get all YAML files in the Algo project, excluding external dependencies."""
        root = Path(__file__).parent.parent.parent
        yaml_files = []

        # Define directories to scan (Algo's actual code)
        algo_dirs = [
            'roles',
            'playbooks',
            'library',
            'files/cloud-init',  # Include cloud-init templates but not CloudFormation
        ]

        # Add root-level YAML files
        yaml_files.extend(root.glob('*.yml'))
        yaml_files.extend(root.glob('*.yaml'))

        # Add YAML files from Algo directories
        for dir_name in algo_dirs:
            dir_path = root / dir_name
            if dir_path.exists():
                yaml_files.extend(dir_path.glob('**/*.yml'))
                yaml_files.extend(dir_path.glob('**/*.yaml'))

        # Exclude patterns
        excluded = [
            '.venv',           # Virtual environment
            '.env',            # Another virtual environment pattern
            'venv',            # Yet another virtual environment
            'test',            # Test files (but keep our own tests)
            'molecule',        # Molecule test files
            'site-packages',   # Python packages
            'ansible_collections',  # External Ansible collections
            'stack.yaml',      # CloudFormation templates (use string booleans by design)
            'stack.yml',       # CloudFormation templates
            '.git',            # Git directory
            '__pycache__',     # Python cache
        ]

        # Filter out excluded paths and CloudFormation templates
        filtered = []
        for f in yaml_files:
            path_str = str(f)
            # Skip if path contains any excluded pattern
            if any(exc in path_str for exc in excluded):
                continue
            # Skip CloudFormation templates in files/ directories
            if '/files/' in path_str and f.name in ['stack.yaml', 'stack.yml']:
                continue
            filtered.append(f)

        return filtered

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
        """Look for patterns that would cause Ansible 12 boolean type issues in Algo code."""
        # These patterns would break Ansible 12's strict boolean checking
        problematic_patterns = [
            (r':\s*["\']true["\']$', "Assigning string 'true' to variable"),
            (r':\s*["\']false["\']$', "Assigning string 'false' to variable"),
            (r'default\(["\']true["\']\)', "Using string 'true' as default"),
            (r'default\(["\']false["\']\)', "Using string 'false' as default"),
        ]

        # Known safe exceptions in Algo
        safe_patterns = [
            'booleans_map',     # This maps string inputs to booleans
            'test_',            # Test files may use different patterns
            'molecule',         # Molecule tests
            'ANSIBLE_',         # Environment variables are strings
            'validate_certs',   # Some modules accept string booleans
            'Default:',         # CloudFormation parameter defaults
        ]

        issues = []

        for yaml_file in self.get_yaml_files():
            # Skip files that aren't Ansible playbooks/tasks/vars
            parts_to_check = ['tasks', 'vars', 'defaults', 'handlers', 'meta', 'playbooks']
            main_files = ['main.yml', 'users.yml', 'server.yml', 'input.yml']
            if not any(part in str(yaml_file) for part in parts_to_check) \
               and yaml_file.name not in main_files:
                continue

            with open(yaml_file) as f:
                lines = f.readlines()

            for i, line in enumerate(lines):
                # Skip comments and empty lines
                stripped_line = line.strip()
                if not stripped_line or stripped_line.startswith('#'):
                    continue

                for pattern, description in problematic_patterns:
                    if re.search(pattern, line):
                        # Check if it's a known safe pattern
                        if not any(safe in line for safe in safe_patterns):
                            # This is a real issue that would break Ansible 12
                            rel_path = yaml_file.relative_to(Path(__file__).parent.parent.parent)
                            issues.append(f"{rel_path}:{i+1}: {description} - {stripped_line}")

        # All Algo code should be fixed
        assert not issues, "Found boolean type issues that would break Ansible 12:\n" + "\n".join(issues[:10])

    def test_verify_our_fixes_are_correct(self):
        """Verify our specific fixes are in place and correct."""
        # Check facts.yml
        facts_file = Path(__file__).parent.parent.parent / "roles/common/tasks/facts.yml"
        with open(facts_file) as f:
            content = f.read()

        # Should use 'is defined', not string literals
        assert 'is defined' in content, "facts.yml should use 'is defined'"
        old_pattern = 'ipv6_support: "{% if ansible_default_ipv6[\'gateway\'] is defined %}'
        old_pattern += 'true{% else %}false{% endif %}"'
        assert old_pattern not in content, "facts.yml still has the old string boolean pattern"

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

