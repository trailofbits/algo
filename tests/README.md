# Tests

## Running Tests

```bash
# Run all linters (same as CI)
ansible-lint . && yamllint . && ruff check . && shellcheck scripts/*.sh

# Run Python unit tests
pytest tests/unit/ -q

# Run privileged E2E connectivity tests after an Algo localhost deployment.
# IPsec requires the generated PKI (`store_pki: true`) and runs a separate
# charon/swanctl client inside a network namespace.
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
| E2E | `test-vpn-connectivity.sh` | Real WireGuard and IPsec handshakes, IKE/CHILD SAs, DNS through each tunnel, routed source IP |

## CI Workflows

| Workflow | Trigger | What It Does |
|----------|---------|--------------|
| `lint.yml` | All PRs | ansible-lint, yamllint, ruff, shellcheck |
| `main.yml` | Push to master | Syntax check, unit tests, Docker build |
| `integration-tests.yml` | PRs to roles/ | Full localhost deployment + E2E tests |
| `smart-tests.yml` | All PRs | Runs subset based on changed files |

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

### Privileged IPsec E2E prerequisites

The IPsec case is not a certificate-only smoke test. It starts a dedicated
`charon` process in `algo-client`, loads the generated CA/certificate/private
key with `swanctl --load-all`, initiates IKEv2, and requires both an
`ESTABLISHED` IKE SA and an `INSTALLED` CHILD SA. It then resolves DNS at
`172.16.0.1` through the tunnel and compares a routed HTTPS request's public
source address with the server's. Set `PUBLIC_IP_URL` to a trusted plain-text
IP endpoint when the default `https://api.ipify.org` is unavailable.

Required Ubuntu packages include `strongswan`, `strongswan-swanctl`,
`libstrongswan-standard-plugins`, `libcharon-extra-plugins`, `iproute2`,
`dnsutils`, and `curl`. The test must run as root on a host that permits network
namespaces and XFRM state. Generated credentials are copied into a mode-0700
temporary directory with mode-0600 files, are never printed or uploaded by the
integration workflow, and are removed by the exit trap.

## Troubleshooting

**E2E tests fail with "namespace already exists"**
```bash
sudo ip netns del algo-client
```

**Template tests fail with "filter not found"**
Add the filter to the mock in `conftest.py`.

**CI fails but local passes**
Check Python/Ansible versions match CI (Python 3.12, Ansible 12+).
