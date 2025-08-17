#!/usr/bin/env python3

import unittest

from jinja2 import Template


class TestPackagePreinstall(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures."""
        # Create a simplified test template with just the packages section
        self.packages_template = Template("""
packages:
  - sudo
{% if performance_preinstall_packages | default(false) %}
  # Universal tools always needed by Algo (performance optimization)
  - git
  - screen
  - apparmor-utils
  - uuid-runtime
  - coreutils
  - iptables-persistent
  - cgroup-tools
{% endif %}
""")

    def test_preinstall_disabled_by_default(self):
        """Test that package pre-installation is disabled by default."""
        # Test with default config (performance_preinstall_packages not set)
        rendered = self.packages_template.render({})

        # Should only have sudo package
        self.assertIn("- sudo", rendered)
        self.assertNotIn("- git", rendered)
        self.assertNotIn("- screen", rendered)
        self.assertNotIn("- apparmor-utils", rendered)

    def test_preinstall_enabled(self):
        """Test that package pre-installation works when enabled."""
        # Test with pre-installation enabled
        rendered = self.packages_template.render({"performance_preinstall_packages": True})

        # Should have sudo and all universal packages
        self.assertIn("- sudo", rendered)
        self.assertIn("- git", rendered)
        self.assertIn("- screen", rendered)
        self.assertIn("- apparmor-utils", rendered)
        self.assertIn("- uuid-runtime", rendered)
        self.assertIn("- coreutils", rendered)
        self.assertIn("- iptables-persistent", rendered)
        self.assertIn("- cgroup-tools", rendered)

    def test_preinstall_disabled_explicitly(self):
        """Test that package pre-installation is disabled when set to false."""
        # Test with pre-installation explicitly disabled
        rendered = self.packages_template.render({"performance_preinstall_packages": False})

        # Should only have sudo package
        self.assertIn("- sudo", rendered)
        self.assertNotIn("- git", rendered)
        self.assertNotIn("- screen", rendered)
        self.assertNotIn("- apparmor-utils", rendered)

    def test_package_count(self):
        """Test that the correct number of packages are included."""
        # Default: should only have sudo (1 package)
        rendered_default = self.packages_template.render({})
        lines_default = [line.strip() for line in rendered_default.split("\n") if line.strip().startswith("- ")]
        self.assertEqual(len(lines_default), 1)

        # Enabled: should have sudo + 7 universal packages (8 total)
        rendered_enabled = self.packages_template.render({"performance_preinstall_packages": True})
        lines_enabled = [line.strip() for line in rendered_enabled.split("\n") if line.strip().startswith("- ")]
        self.assertEqual(len(lines_enabled), 8)


if __name__ == "__main__":
    unittest.main()
