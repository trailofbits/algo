"""Shared pytest fixtures for Algo VPN tests."""

import base64
import secrets
import sys
import tempfile
from pathlib import Path

import pytest
import yaml

# Add library directory to path for custom module imports
sys.path.insert(0, str(Path(__file__).parent.parent / "library"))


@pytest.fixture
def test_variables():
    """Load test variables from YAML fixture."""
    fixture_path = Path(__file__).parent / "fixtures" / "test_variables.yml"
    with open(fixture_path) as f:
        return yaml.safe_load(f)


@pytest.fixture
def test_config(test_variables):
    """Get test configuration with common defaults."""
    return test_variables.copy()


@pytest.fixture
def temp_directory():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def wireguard_private_key():
    """Generate a random WireGuard-compatible private key."""
    raw_key = secrets.token_bytes(32)
    return base64.b64encode(raw_key).decode()


@pytest.fixture
def wireguard_key_pair(temp_directory):
    """Generate a WireGuard key pair and return paths and values."""
    raw_key = secrets.token_bytes(32)
    b64_key = base64.b64encode(raw_key).decode()

    private_key_path = temp_directory / "private.key"
    private_key_path.write_bytes(raw_key)

    return {
        "private_key_raw": raw_key,
        "private_key_b64": b64_key,
        "private_key_path": str(private_key_path),
    }


class MockAnsibleModule:
    """Mock AnsibleModule for testing custom Ansible modules."""

    def __init__(self, params):
        """Initialize with module parameters."""
        self.params = params
        self.result = {}
        self.failed = False
        self.fail_msg = None

    def fail_json(self, **kwargs):
        """Record failure and raise exception."""
        self.failed = True
        self.fail_msg = kwargs.get("msg", "Unknown error")
        raise Exception(f"Module failed: {self.fail_msg}")

    def exit_json(self, **kwargs):
        """Record successful result."""
        self.result = kwargs


@pytest.fixture
def mock_ansible_module():
    """Fixture providing MockAnsibleModule class."""
    return MockAnsibleModule


# Jinja2 mock filters for template testing
def mock_to_uuid(value):
    """Mock the to_uuid filter."""
    return "12345678-1234-5678-1234-567812345678"


def mock_bool(value):
    """Mock the bool filter."""
    return str(value).lower() in ("true", "1", "yes", "on")


def mock_lookup(lookup_type, path):
    """Mock the lookup function."""
    if lookup_type == "file":
        if "private" in path:
            return "MOCK_PRIVATE_KEY_BASE64=="
        elif "public" in path:
            return "MOCK_PUBLIC_KEY_BASE64=="
        elif "preshared" in path:
            return "MOCK_PRESHARED_KEY_BASE64=="
    return "MOCK_LOOKUP_DATA"


@pytest.fixture
def jinja2_env():
    """Create a Jinja2 environment with mock Ansible filters."""
    from jinja2 import Environment, FileSystemLoader, StrictUndefined

    def create_env(template_dir):
        env = Environment(loader=FileSystemLoader(template_dir), undefined=StrictUndefined)
        env.globals["lookup"] = mock_lookup
        env.filters["to_uuid"] = mock_to_uuid
        env.filters["bool"] = mock_bool
        return env

    return create_env


@pytest.fixture
def project_root():
    """Return the project root directory."""
    return Path(__file__).parent.parent


@pytest.fixture
def roles_dir(project_root):
    """Return the roles directory."""
    return project_root / "roles"


# Skip markers for conditional tests
def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line("markers", "requires_wireguard: mark test as requiring WireGuard tools")
    config.addinivalue_line("markers", "slow: mark test as slow running")


@pytest.fixture(autouse=True)
def skip_wireguard_tests(request):
    """Skip tests marked with requires_wireguard if WireGuard tools aren't available."""
    if request.node.get_closest_marker("requires_wireguard"):
        import shutil

        if not shutil.which("wg"):
            pytest.skip("WireGuard tools not available")
