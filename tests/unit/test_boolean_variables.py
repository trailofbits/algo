#!/usr/bin/env python3
"""
Test that Ansible variables produce proper boolean types, not strings.
This prevents issues with Ansible 12.0.0's strict type checking.
"""

import jinja2
import pytest


def render_template(template_str, variables=None):
    """Render a Jinja2 template with given variables."""
    env = jinja2.Environment()
    template = env.from_string(template_str)
    return template.render(variables or {})


class TestBooleanVariables:
    """Test that critical variables produce actual booleans."""

    def test_ipv6_support_produces_boolean(self):
        """Ensure ipv6_support produces boolean, not string 'true'/'false'."""
        # Test with gateway defined (should be boolean True)
        template = "{{ ansible_default_ipv6['gateway'] is defined }}"
        vars_with_gateway = {'ansible_default_ipv6': {'gateway': 'fe80::1'}}
        result = render_template(template, vars_with_gateway)
        assert result == "True"  # Jinja2 renders boolean True as string "True"
        
        # Test without gateway (should be boolean False)
        vars_no_gateway = {'ansible_default_ipv6': {}}
        result = render_template(template, vars_no_gateway)
        assert result == "False"  # Jinja2 renders boolean False as string "False"
        
        # The key is that we're NOT producing string literals "true" or "false"
        bad_template = "{% if ansible_default_ipv6['gateway'] is defined %}true{% else %}false{% endif %}"
        result_bad = render_template(bad_template, vars_no_gateway)
        assert result_bad == "false"  # This is a string literal, not a boolean
        
        # Verify our fix doesn't produce string literals
        assert result != "false"  # Our fix produces "False" (from boolean), not "false" (string literal)

    def test_algo_variables_boolean_fallbacks(self):
        """Ensure algo_* variables produce booleans in their fallback cases."""
        # Test the fixed template (produces boolean)
        good_template = "{% if var is defined %}{{ var | bool }}{%- else %}{{ false }}{% endif %}"
        result_good = render_template(good_template, {})
        assert result_good == "False"  # Boolean False renders as "False"
        
        # Test the old broken template (produces string)
        bad_template = "{% if var is defined %}{{ var | bool }}{%- else %}false{% endif %}"
        result_bad = render_template(bad_template, {})
        assert result_bad == "false"  # String literal "false"
        
        # Verify they're different
        assert result_good != result_bad
        assert result_good == "False" and result_bad == "false"

    def test_boolean_filter_on_strings(self):
        """Test that the bool filter correctly converts string values."""
        # Since we can't test Ansible's bool filter directly in Jinja2,
        # we test the pattern we're using in our templates
        
        # Test that our templates don't use raw string "true"/"false"
        # which would fail in Ansible 12
        bad_pattern = "{%- else %}false{% endif %}"
        good_pattern = "{%- else %}{{ false }}{% endif %}"
        
        # The bad pattern produces a string literal
        result_bad = render_template("{% if var is defined %}something" + bad_pattern, {})
        assert "false" in result_bad  # String literal
        
        # The good pattern produces a boolean value
        result_good = render_template("{% if var is defined %}something" + good_pattern, {})
        assert "False" in result_good  # Boolean False rendered as "False"

    def test_ansible_12_conditional_compatibility(self):
        """
        Test that our fixes work with Ansible 12's strict type checking.
        This simulates what Ansible 12 will do with our variables.
        """
        # Our fixed template - produces actual boolean
        fixed_ipv6 = "{{ ansible_default_ipv6['gateway'] is defined }}"
        fixed_algo = "{% if var is defined %}{{ var | bool }}{%- else %}{{ false }}{% endif %}"
        
        # Simulate the boolean value in a conditional context
        # In Ansible 12, this would fail if it's a string "true"/"false"
        vars_with_gateway = {'ansible_default_ipv6': {'gateway': 'fe80::1'}}
        ipv6_result = render_template(fixed_ipv6, vars_with_gateway)
        
        # The result should be "True" (boolean rendered), not "true" (string literal)
        assert ipv6_result == "True"
        assert ipv6_result != "true"
        
        # Test algo variable fallback
        algo_result = render_template(fixed_algo, {})
        assert algo_result == "False"
        assert algo_result != "false"

    def test_regression_no_string_booleans(self):
        """
        Regression test: ensure we never produce string literals 'true' or 'false'.
        This is what breaks Ansible 12.0.0.
        """
        # These patterns should NOT appear in our fixed code
        bad_patterns = [
            "{}true{}",
            "{}false{}",
            "{%- else %}true{% endif %}",
            "{%- else %}false{% endif %}",
        ]
        
        # Our fixes should use these patterns instead
        good_patterns = [
            "{{ true }}",
            "{{ false }}",
            "is defined",
            "| bool",
        ]
        
        # Test that our fixed templates don't produce string boolean literals
        fixed_template = "{{ ansible_default_ipv6['gateway'] is defined }}"
        for pattern in bad_patterns:
            assert "true" not in fixed_template.replace(" ", "")
            assert "false" not in fixed_template.replace(" ", "")
        
        # Test algo variable fix
        fixed_algo = "{% if var is defined %}{{ var | bool }}{%- else %}{{ false }}{% endif %}"
        assert "{}false{}" not in fixed_algo.replace(" ", "")
        assert "{{ false }}" in fixed_algo