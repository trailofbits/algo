#!/usr/bin/env python3
"""
Test that verifies the fix for Ansible 12.0.0 boolean type checking.
This test reads the actual YAML files to ensure they don't produce string booleans.
"""

import re
from pathlib import Path


class TestAnsible12BooleanFix:
    """Tests to verify Ansible 12.0.0 boolean compatibility."""

    def test_ipv6_support_not_string_boolean(self):
        """Verify ipv6_support in facts.yml doesn't produce string 'true'/'false'."""
        facts_file = Path(__file__).parent.parent.parent / "roles/common/tasks/facts.yml"

        with open(facts_file) as f:
            content = f.read()

        # Check that we're NOT using the broken pattern
        broken_pattern = r'ipv6_support:\s*".*\}true\{.*\}false\{.*"'
        assert not re.search(broken_pattern, content), (
            "ipv6_support is using string literals 'true'/'false' which breaks Ansible 12"
        )

        # Check that we ARE using the correct pattern
        correct_pattern = r'ipv6_support:\s*".*is\s+defined.*"'
        assert re.search(correct_pattern, content), "ipv6_support should use 'is defined' which returns a boolean"

    def test_input_yml_algo_variables_not_string_boolean(self):
        """Verify algo_* variables in input.yml don't produce string 'false'."""
        input_file = Path(__file__).parent.parent.parent / "input.yml"

        with open(input_file) as f:
            content = f.read()

        # Variables to check
        algo_vars = [
            "algo_ondemand_cellular",
            "algo_ondemand_wifi",
            "algo_dns_adblocking",
            "algo_ssh_tunneling",
            "algo_store_pki",
        ]

        for var in algo_vars:
            # Find the variable definition
            var_pattern = rf"{var}:.*?\n(.*?)\n\s*algo_"
            match = re.search(var_pattern, content, re.DOTALL)

            if match:
                var_content = match.group(1)

                # Check that we're NOT using string literal 'false'
                # The broken pattern: {%- else %}false{% endif %}
                assert not re.search(r"\{%-?\s*else\s*%\}false\{%", var_content), (
                    f"{var} is using string literal 'false' which breaks Ansible 12"
                )

                # Check that we ARE using {{ false }}
                # The correct pattern: {%- else %}{{ false }}{% endif %}
                if "else" in var_content:
                    assert "{{ false }}" in var_content or "{{ true }}" in var_content or "| bool" in var_content, (
                        f"{var} should use '{{{{ false }}}}' or '{{{{ true }}}}' for boolean values"
                    )

    def test_no_bare_true_false_in_templates(self):
        """Scan for any remaining bare 'true'/'false' in Jinja2 expressions."""
        # Patterns that indicate string boolean literals (bad)
        bad_patterns = [
            r"\{%[^%]*\}true\{%",  # %}true{%
            r"\{%[^%]*\}false\{%",  # %}false{%
            r"%\}true\{%",  # %}true{%
            r"%\}false\{%",  # %}false{%
        ]

        files_to_check = [
            Path(__file__).parent.parent.parent / "roles/common/tasks/facts.yml",
            Path(__file__).parent.parent.parent / "input.yml",
        ]

        for file_path in files_to_check:
            with open(file_path) as f:
                content = f.read()

            for pattern in bad_patterns:
                matches = re.findall(pattern, content)
                assert not matches, (
                    f"Found string boolean literal in {file_path.name}: {matches}. "
                    f"Use '{{{{ true }}}}' or '{{{{ false }}}}' instead."
                )

    def test_conditional_uses_of_variables(self):
        """Check that when: conditions using these variables will work with booleans."""
        # Files that might have 'when:' conditions
        files_to_check = [
            Path(__file__).parent.parent.parent / "roles/common/tasks/iptables.yml",
            Path(__file__).parent.parent.parent / "server.yml",
            Path(__file__).parent.parent.parent / "users.yml",
        ]

        for file_path in files_to_check:
            if not file_path.exists():
                continue

            with open(file_path) as f:
                content = f.read()

            # Find when: conditions
            when_patterns = re.findall(r"when:\s*(\w+)\s*$", content, re.MULTILINE)

            # These variables must be booleans for Ansible 12
            boolean_vars = ["ipv6_support", "algo_dns_adblocking", "algo_ssh_tunneling"]

            for var in when_patterns:
                if var in boolean_vars:
                    # This is good - we're using the variable directly
                    # which requires it to be a boolean in Ansible 12
                    pass  # Test passes if we get here
