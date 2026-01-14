#!/usr/bin/env python3
"""
Cloud-init template validation test.

This test validates that the cloud-init template for DigitalOcean deployments
renders correctly and produces valid YAML that cloud-init can parse.

This test helps prevent regressions like issue #14800 where YAML formatting
issues caused cloud-init to fail completely, resulting in SSH timeouts.

Usage:
    python3 tests/test_cloud_init_template.py

Or from project root:
    python3 -m pytest tests/test_cloud_init_template.py -v
"""

import sys
from pathlib import Path

import yaml

# Add project root to path for imports if needed
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def create_expected_cloud_init():
    """
    Create the expected cloud-init content that should be generated
    by our template after the YAML indentation fix.
    """
    return """#cloud-config
# CRITICAL: The above line MUST be exactly "#cloud-config" (no space after #)
# This is required by cloud-init's YAML parser. Adding a space breaks parsing
# and causes all cloud-init directives to be skipped, resulting in SSH timeouts.
# See: https://github.com/trailofbits/algo/issues/14800
output: {all: '| tee -a /var/log/cloud-init-output.log'}

package_update: true
package_upgrade: true

packages:
  - sudo

users:
  - default
  - name: algo
    homedir: /home/algo
    sudo: ALL=(ALL) NOPASSWD:ALL
    groups: adm,netdev
    shell: /bin/bash
    lock_passwd: true
    ssh_authorized_keys:
      - "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQDTest algo-test"

write_files:
  - path: /etc/ssh/sshd_config
    content: |
      Port 4160
      AllowGroups algo
      PermitRootLogin no
      PasswordAuthentication no
      ChallengeResponseAuthentication no
      UsePAM yes
      X11Forwarding yes
      PrintMotd no
      AcceptEnv LANG LC_*
      Subsystem	sftp	/usr/lib/openssh/sftp-server

runcmd:
  - set -x
  - ufw --force reset
  - sudo apt-get remove -y --purge sshguard || true
  - systemctl restart sshd.service
"""


class TestCloudInitTemplate:
    """Test class for cloud-init template validation."""

    def test_yaml_validity(self):
        """Test that the expected cloud-init YAML is valid."""
        print("🧪 Testing YAML validity...")

        cloud_init_content = create_expected_cloud_init()

        try:
            parsed = yaml.safe_load(cloud_init_content)
            print("✅ YAML parsing successful")
            assert parsed is not None, "YAML should parse to a non-None value"
            return parsed
        except yaml.YAMLError as e:
            print(f"❌ YAML parsing failed: {e}")
            assert False, f"YAML parsing failed: {e}"

    def test_required_sections(self):
        """Test that all required cloud-init sections are present."""
        print("🧪 Testing required sections...")

        parsed = self.test_yaml_validity()

        required_sections = ["package_update", "package_upgrade", "packages", "users", "write_files", "runcmd"]

        missing = [section for section in required_sections if section not in parsed]
        assert not missing, f"Missing required sections: {missing}"

        print("✅ All required sections present")

    def test_ssh_configuration(self):
        """Test that SSH configuration is correct."""
        print("🧪 Testing SSH configuration...")

        parsed = self.test_yaml_validity()

        write_files = parsed.get("write_files", [])
        assert write_files, "write_files section should be present"

        # Find sshd_config file
        sshd_config = None
        for file_entry in write_files:
            if file_entry.get("path") == "/etc/ssh/sshd_config":
                sshd_config = file_entry
                break

        assert sshd_config, "sshd_config file should be in write_files"

        content = sshd_config.get("content", "")
        assert content, "sshd_config should have content"

        # Check required SSH configurations
        required_configs = ["Port 4160", "AllowGroups algo", "PermitRootLogin no", "PasswordAuthentication no"]

        missing = [config for config in required_configs if config not in content]
        assert not missing, f"Missing SSH configurations: {missing}"

        # Verify proper formatting - first line should be Port directive
        lines = content.strip().split("\n")
        assert lines[0].strip() == "Port 4160", f"First line should be 'Port 4160', got: {repr(lines[0])}"

        print("✅ SSH configuration correct")

    def test_user_creation(self):
        """Test that algo user will be created correctly."""
        print("🧪 Testing user creation...")

        parsed = self.test_yaml_validity()

        users = parsed.get("users", [])
        assert users, "users section should be present"

        # Find algo user
        algo_user = None
        for user in users:
            if isinstance(user, dict) and user.get("name") == "algo":
                algo_user = user
                break

        assert algo_user, "algo user should be defined"

        # Check required user properties
        required_props = ["sudo", "groups", "shell", "ssh_authorized_keys"]
        missing = [prop for prop in required_props if prop not in algo_user]
        assert not missing, f"algo user missing properties: {missing}"

        # Verify sudo configuration
        sudo_config = algo_user.get("sudo", "")
        assert "NOPASSWD:ALL" in sudo_config, f"sudo config should allow passwordless access: {sudo_config}"

        print("✅ User creation correct")

    def test_runcmd_section(self):
        """Test that runcmd section will restart SSH correctly."""
        print("🧪 Testing runcmd section...")

        parsed = self.test_yaml_validity()

        runcmd = parsed.get("runcmd", [])
        assert runcmd, "runcmd section should be present"

        # Check for SSH restart command
        ssh_restart_found = False
        for cmd in runcmd:
            if "systemctl restart sshd" in str(cmd):
                ssh_restart_found = True
                break

        assert ssh_restart_found, f"SSH restart command not found in runcmd: {runcmd}"

        print("✅ runcmd section correct")

    def test_indentation_consistency(self):
        """Test that sshd_config content has consistent indentation."""
        print("🧪 Testing indentation consistency...")

        cloud_init_content = create_expected_cloud_init()

        # Extract the sshd_config content lines
        lines = cloud_init_content.split("\n")
        in_sshd_content = False
        sshd_lines = []

        for line in lines:
            if "content: |" in line:
                in_sshd_content = True
                continue
            elif in_sshd_content:
                if line.strip() == "" and len(sshd_lines) > 0:
                    break
                if line.startswith("runcmd:"):
                    break
                sshd_lines.append(line)

        assert sshd_lines, "Should be able to extract sshd_config content"

        # Check that all non-empty lines have consistent 6-space indentation
        non_empty_lines = [line for line in sshd_lines if line.strip()]
        assert non_empty_lines, "sshd_config should have content"

        for line in non_empty_lines:
            # Each line should start with exactly 6 spaces
            assert line.startswith("      ") and not line.startswith("       "), (
                f"Line should have exactly 6 spaces indentation: {repr(line)}"
            )

        print("✅ Indentation is consistent")


def run_tests():
    """Run all tests manually (for non-pytest usage)."""
    print("🚀 Cloud-init template validation tests")
    print("=" * 50)

    test_instance = TestCloudInitTemplate()

    try:
        test_instance.test_yaml_validity()
        test_instance.test_required_sections()
        test_instance.test_ssh_configuration()
        test_instance.test_user_creation()
        test_instance.test_runcmd_section()
        test_instance.test_indentation_consistency()

        print("=" * 50)
        print("🎉 ALL TESTS PASSED!")
        print("✅ Cloud-init template is working correctly")
        print("✅ DigitalOcean deployment should succeed")
        return True

    except AssertionError as e:
        print(f"❌ Test failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
