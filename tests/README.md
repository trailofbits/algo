# Tests

Run the same checks locally and in CI:

```bash
./scripts/lint.sh
uv run --locked pytest -q
```

The Python suite executes production Ansible tasks in temporary directories. It does not
install VPN services or change the host network. Ansible failures and invalid output fail the tests.

| Location | Coverage |
|----------|----------|
| `library/test_x25519_pubkey.py` | Real key derivation, binary input boundaries, and module errors |
| `test_ansible_smoke.py` | Input handling, inventory, keys, WireGuard configs, Apple profiles, SSH, and cloud-init |
| `test_wireguard_qr.py` | QR generation without the Segno CLI on PATH, private file permissions, and write failures |
| `test_adblock.py` | Atomic blocklist refresh and preservation after network or write failures |
| `test_algo_launcher.py` | CLI help, dependency failures, and locked dependency installation |
| `test_destroy_paths.py` | Actual destroy playbook rejection of paths outside the config directory |
| `test_ipsec_certificate_chain.py` | Generated CA restrictions, server/client purposes, chains, keys, and encrypted PKCS#12 exports |
| `test_user_preflight.py` | User-update identity and SSH connectivity checks |
| `network/` | Host firewall rules, cloud ingress requests, DNS rebinding protection, and protocol combinations |
| `unit/` | Configuration, template, provider, and server-list regressions |
| `e2e/` | Deployed WireGuard connectivity, plus IPsec certificate and service checks |

Certificate tests generate fresh IPv4 and dual-stack PKI in temporary directories. They never read
saved deployments under `configs/`. OpenSSL verifies the chains and encrypted client exports.
The tests also inspect the exact subject alternative names, so unexpected IP identities fail
even on macOS LibreSSL, whose `verify` command lacks OpenSSL's `-verify_ip` option.

Cloud ingress tests render the actual provider requests without creating cloud resources.
Google Cloud retains both VPN protocols because its firewall is shared across deployments.
The smoke test parses generated Apple profiles and checks that they contain the same client keys
and connection settings as the generated WireGuard configuration.

## Network runtime tests

The required Docker CI job checks IPv4 and IPv6 rules with `iptables-restore`, sends DNS responses
through DNSCrypt proxy, and decodes generated QR images. The DNS server runs locally with a
temporary TLS certificate; DNS tests do not contact public resolvers. These tests require Linux,
network administration capability, and the named tools. Run them in a disposable container:

```bash
docker build -t local/algo:test .
docker run --rm --cap-add=NET_ADMIN \
  -e UV_NO_DEV=false -e ALGO_NETWORK_RUNTIME=1 \
  -v "$PWD/tests:/algo/tests:ro" \
  -v "$PWD/config.cfg:/algo/config.cfg:ro" \
  --entrypoint /bin/sh local/algo:test -ec '
    apk add --no-cache iptables dnscrypt-proxy zbar imagemagick
    uv run --locked pytest -q tests/network tests/test_wireguard_qr.py
  '
```

The regular Python suite skips tests that require this container. Setting `ALGO_NETWORK_RUNTIME=1`
makes missing runtime tools fail the tests. The shipped image excludes development dependencies;
the command installs them only in the disposable test container.

## CI workflows

| Workflow | Trigger | Checks |
|----------|---------|--------|
| `main.yml` | Pull requests and main/master pushes | Hooks, Python and Ansible tests, PowerShell lint, audit, Docker and network tests |
| `integration-tests.yml` | Pull requests affecting deployment files | Localhost deployment and E2E checks |

CI runs every hook in `.pre-commit-config.yaml`. Python tools and the hook runner use `uv.lock`;
prek installs the remaining pinned tools. The `All Required Tests` job requires every CI job to pass.

For deployed VPN checks, see [E2E tests](e2e/README.md). IPsec checks currently verify certificates
and service availability; they do not establish a client tunnel.

## Writing tests

Exercise production modules, tasks, or templates. Parse their output and assert the expected
behavior, including failure paths. Use Ansible's actual filters when rendering templates.
Avoid tests that validate a copied configuration string or replace the logic under test with a mock.

Keep regressions next to the relevant test group. Verify that a test fails when the behavior it
protects is temporarily broken, then restore the code and run the checks again.
