#!/usr/bin/env python3
"""
Basic sanity tests for Algo VPN that don't require deployment
"""
import os
import sys
import yaml
import subprocess


def test_python_version():
    """Ensure we're running on Python 3.10+"""
    assert sys.version_info >= (3, 10), f"Python 3.10+ required, got {sys.version}"
    print("✓ Python version check passed")


def test_requirements_file_exists():
    """Check that requirements.txt exists"""
    assert os.path.exists("requirements.txt"), "requirements.txt not found"
    print("✓ requirements.txt exists")


def test_config_file_valid():
    """Check that config.cfg is valid YAML"""
    assert os.path.exists("config.cfg"), "config.cfg not found"
    
    with open("config.cfg", "r") as f:
        try:
            config = yaml.safe_load(f)
            assert isinstance(config, dict), "config.cfg should parse as a dictionary"
            print("✓ config.cfg is valid YAML")
        except yaml.YAMLError as e:
            raise AssertionError(f"config.cfg is not valid YAML: {e}")


def test_ansible_syntax():
    """Check that main playbook has valid syntax"""
    result = subprocess.run(
        ["ansible-playbook", "main.yml", "--syntax-check"],
        capture_output=True,
        text=True
    )
    
    assert result.returncode == 0, f"Ansible syntax check failed:\n{result.stderr}"
    print("✓ Ansible playbook syntax is valid")


def test_shellcheck():
    """Run shellcheck on shell scripts"""
    shell_scripts = ["algo", "install.sh"]
    
    for script in shell_scripts:
        if os.path.exists(script):
            result = subprocess.run(
                ["shellcheck", script],
                capture_output=True,
                text=True
            )
            assert result.returncode == 0, f"Shellcheck failed for {script}:\n{result.stdout}"
            print(f"✓ {script} passed shellcheck")


def test_dockerfile_exists():
    """Check that Dockerfile exists and is not empty"""
    assert os.path.exists("Dockerfile"), "Dockerfile not found"
    
    with open("Dockerfile", "r") as f:
        content = f.read()
        assert len(content) > 100, "Dockerfile seems too small"
        assert "FROM" in content, "Dockerfile missing FROM statement"
    
    print("✓ Dockerfile exists and looks valid")


if __name__ == "__main__":
    # Change to repo root
    os.chdir(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    
    tests = [
        test_python_version,
        test_requirements_file_exists,
        test_config_file_valid,
        test_ansible_syntax,
        test_shellcheck,
        test_dockerfile_exists,
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
        print(f"\nAll {len(tests)} tests passed!")