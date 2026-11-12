# Tests

## Running Tests

```bash
# Run all linters (same as CI)
./scripts/lint.sh

# Run the full Python test suite
uv run --locked pytest -q

# Run the Ansible runtime smoke test on its own
uv run --locked pytest -q tests/test_ansible_smoke.py

# Run E2E connectivity tests (requires deployed Algo on localhost)
sudo tests/e2e/test-vpn-connectivity.sh both
```

## Directory Structure

```
tests/
├── unit/                    # Python unit tests (pytest)
│   ├── test_basic_sanity.py
│   ├── test_config_validation.py
│   ├── test_template_rendering.py
│   └── ...
├── e2e/                     # End-to-end connectivity tests
│   └── test-vpn-connectivity.sh
├── integration/             # Integration test helpers
│   └── mock_modules/
├── fixtures/                # Shared test data
│   └── test_variables.yml
└── conftest.py              # Pytest configuration
```

## Test Coverage

| Category | Tests | What's Verified |
|----------|-------|-----------------|
| Sanity | `test_basic_sanity.py` | Python version, config syntax, playbook validity |
| Config | `test_config_validation.py` | WireGuard/IPsec config formats, key validation |
| Templates | `test_template_rendering.py` | Jinja2 template syntax, filter compatibility |
| Certificates | `test_certificate_validation.py` | OpenSSL compatibility, PKCS#12 export |
| Cloud Providers | `test_cloud_provider_configs.py` | Region formats, instance types, OS images |
| Ansible runtime | `test_ansible_smoke.py` | Input handling, inventory, real keys, client rendering |
| E2E | `test-vpn-connectivity.sh` | WireGuard handshake, IPsec connection, DNS through VPN |

## CI Workflows

| Workflow | Trigger | What It Does |
|----------|---------|--------------|
| `main.yml` | PRs and main/master pushes | Hooks, Python, PowerShell, audit, Docker |
| `integration-tests.yml` | PRs to roles/ | Full localhost deployment + E2E tests |
| `test-effectiveness.yml` | Weekly or manual | Report artifact and workflow summary |

CI runs every hook in `.pre-commit-config.yaml`. Python tools and the hook runner use `uv.lock`;
prek installs the remaining pinned hook tools. The final CI job requires every check to succeed.

The Python suite runs the Ansible smoke playbook on every PR, including dependency updates. It
executes production tasks and renders a client configuration in a temporary directory without
installing services or changing the host network. Ansible errors and invalid output fail the test.

## Writing Tests

### Python Unit Tests

Place in `tests/unit/`. Use fixtures from `conftest.py`:

```python
def test_something(mock_ansible_module, jinja_env):
    # mock_ansible_module - mocked AnsibleModule
    # jinja_env - Jinja2 environment with Ansible filters
    pass
```

### Shell Scripts

Use bash strict mode and pass shellcheck:

```bash
#!/bin/bash
set -euo pipefail
```

## Troubleshooting

**E2E tests fail with "namespace already exists"**
```bash
sudo ip netns del algo-client
```

**Template tests fail with "filter not found"**
Add the filter to the mock in `conftest.py`.

**CI fails but local passes**
Check Python/Ansible versions match CI (Python 3.11, Ansible 12+).
