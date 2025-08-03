#!/usr/bin/env python3
"""
Test that Docker image builds and starts correctly
"""
import subprocess
import sys


def test_docker_build():
    """Build the Docker image"""
    print("Building Docker image...")
    result = subprocess.run(
        ["docker", "build", "-t", "algo-test:ci", "."],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print(f"Docker build failed:\n{result.stderr}")
        return False

    print("✓ Docker build succeeded")
    return True


def test_docker_run():
    """Test that the Docker container can start"""
    print("Testing Docker container...")

    # Test that the container can show help
    result = subprocess.run(
        ["docker", "run", "--rm", "algo-test:ci", "/algo/algo", "--help"],
        capture_output=True,
        text=True
    )

    if result.returncode != 0 or "usage: ansible-playbook" not in result.stdout:
        print(f"Docker run failed:\n{result.stderr}")
        return False

    print("✓ Docker container runs successfully")
    return True


def test_docker_ansible_version():
    """Test that Ansible is installed in the container"""
    print("Checking Ansible version in container...")

    # Ansible is installed in a virtualenv in the container
    result = subprocess.run(
        ["docker", "run", "--rm", "--entrypoint", "/bin/sh", "algo-test:ci",
         "-c", "source /algo/.env/bin/activate && ansible --version"],
        capture_output=True,
        text=True
    )

    if result.returncode != 0 or "ansible" not in result.stdout:
        print(f"Ansible check failed:\n{result.stderr}")
        return False

    version_line = result.stdout.split('\n')[0]
    print(f"✓ {version_line}")
    return True


if __name__ == "__main__":
    tests = [
        test_docker_build,
        test_docker_run,
        test_docker_ansible_version,
    ]

    failed = 0
    for test in tests:
        try:
            if not test():
                failed += 1
        except Exception as e:
            print(f"✗ {test.__name__} error: {e}")
            failed += 1

    if failed > 0:
        print(f"\n{failed} tests failed")
        sys.exit(1)
    else:
        print(f"\nAll {len(tests)} tests passed!")
