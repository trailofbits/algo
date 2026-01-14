#!/usr/bin/env python
"""
Test for AWS Lightsail boto3 parameter fix.
Verifies that get_aws_connection_info() works without the deprecated boto3 parameter.
Addresses issue #14822.
"""

import importlib.util
import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Add the library directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../library"))


class TestLightsailBoto3Fix(unittest.TestCase):
    """Test that lightsail_region_facts.py works without boto3 parameter."""

    def setUp(self):
        """Set up test fixtures."""
        # Mock the ansible module_utils since we're testing outside of Ansible
        self.mock_modules = {
            "ansible.module_utils.basic": MagicMock(),
            "ansible.module_utils.ec2": MagicMock(),
            "ansible.module_utils.aws.core": MagicMock(),
        }

        # Apply mocks
        self.patches = []
        for module_name, mock_module in self.mock_modules.items():
            patcher = patch.dict("sys.modules", {module_name: mock_module})
            patcher.start()
            self.patches.append(patcher)

    def tearDown(self):
        """Clean up patches."""
        for patcher in self.patches:
            patcher.stop()

    def test_lightsail_region_facts_imports(self):
        """Test that lightsail_region_facts can be imported."""
        try:
            # Import the module
            spec = importlib.util.spec_from_file_location(
                "lightsail_region_facts",
                os.path.join(os.path.dirname(__file__), "../../library/lightsail_region_facts.py"),
            )
            module = importlib.util.module_from_spec(spec)

            # This should not raise an error
            spec.loader.exec_module(module)

            # Verify the module loaded
            self.assertIsNotNone(module)
            self.assertTrue(hasattr(module, "main"))

        except Exception as e:
            self.fail(f"Failed to import lightsail_region_facts: {e}")

    def test_get_aws_connection_info_called_without_boto3(self):
        """Test that get_aws_connection_info is called without boto3 parameter."""
        # Mock get_aws_connection_info to track calls
        mock_get_aws_connection_info = MagicMock(return_value=("us-west-2", None, {}))

        with patch("ansible.module_utils.ec2.get_aws_connection_info", mock_get_aws_connection_info):
            # Import the module
            spec = importlib.util.spec_from_file_location(
                "lightsail_region_facts",
                os.path.join(os.path.dirname(__file__), "../../library/lightsail_region_facts.py"),
            )
            module = importlib.util.module_from_spec(spec)

            # Mock AnsibleModule
            mock_ansible_module = MagicMock()
            mock_ansible_module.params = {}
            mock_ansible_module.check_mode = False

            with patch("ansible.module_utils.basic.AnsibleModule", return_value=mock_ansible_module):
                # Execute the module
                try:
                    spec.loader.exec_module(module)
                    module.main()
                except SystemExit:
                    # Module calls exit_json or fail_json which raises SystemExit
                    pass
                except Exception:
                    # We expect some exceptions since we're mocking, but we want to check the call
                    pass

            # Verify get_aws_connection_info was called
            if mock_get_aws_connection_info.called:
                # Get the call arguments
                call_args = mock_get_aws_connection_info.call_args

                # Ensure boto3=True is NOT in the arguments
                if call_args:
                    # Check positional arguments
                    if call_args[0]:  # args
                        self.assertTrue(
                            len(call_args[0]) <= 1,
                            "get_aws_connection_info should be called with at most 1 positional arg (module)",
                        )

                    # Check keyword arguments
                    if call_args[1]:  # kwargs
                        self.assertNotIn(
                            "boto3", call_args[1], "get_aws_connection_info should not be called with boto3 parameter"
                        )

    def test_no_boto3_parameter_in_source(self):
        """Verify that boto3 parameter is not present in the source code."""
        lightsail_path = os.path.join(os.path.dirname(__file__), "../../library/lightsail_region_facts.py")

        with open(lightsail_path) as f:
            content = f.read()

        # Check that boto3=True is not in the file
        self.assertNotIn(
            "boto3=True", content, "boto3=True parameter should not be present in lightsail_region_facts.py"
        )

        # Check that boto3 parameter is not used with get_aws_connection_info
        self.assertNotIn(
            "get_aws_connection_info(module, boto3",
            content,
            "get_aws_connection_info should not be called with boto3 parameter",
        )

    def test_regression_issue_14822(self):
        """
        Regression test for issue #14822.
        Ensures that the deprecated boto3 parameter is not used.
        """
        # This test documents the specific issue that was fixed
        # The boto3 parameter was deprecated and removed in amazon.aws collection
        # that comes with Ansible 11.x

        lightsail_path = os.path.join(os.path.dirname(__file__), "../../library/lightsail_region_facts.py")

        with open(lightsail_path) as f:
            lines = f.readlines()

        # Find the line that calls get_aws_connection_info
        for line_num, line in enumerate(lines, 1):
            if "get_aws_connection_info" in line and "region" in line:
                # This should be around line 85
                # Verify it doesn't have boto3=True
                self.assertNotIn("boto3", line, f"Line {line_num} should not contain boto3 parameter")

                # Verify the correct format
                self.assertIn(
                    "get_aws_connection_info(module)",
                    line,
                    f"Line {line_num} should call get_aws_connection_info(module) without boto3",
                )
                break
        else:
            self.fail("Could not find get_aws_connection_info call in lightsail_region_facts.py")


if __name__ == "__main__":
    unittest.main()
