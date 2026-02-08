# CLAUDE.md - LLM Guidance for Algo VPN

This document provides essential context and guidance for LLMs working on the Algo VPN codebase.

## Project Overview

Algo is an Ansible-based tool that sets up a personal VPN in the cloud. It's designed to be:
- **Security-focused**: Creates hardened VPN servers with minimal attack surface
- **Easy to use**: Automated deployment with sensible defaults
- **Multi-platform**: Supports various cloud providers and operating systems
- **Privacy-preserving**: No logging, minimal data retention

### Core Technologies
- **VPN Protocols**: WireGuard (preferred) and IPsec/IKEv2
- **Configuration Management**: Ansible (v12+)
- **Languages**: Python, YAML, Shell, Jinja2 templates
- **Supported Providers**: AWS, Azure, DigitalOcean, GCP, Vultr, Hetzner, local deployment

### Philosophy
- Stability over features
- Security over convenience
- Clarity over cleverness
- Test everything
- Stay in scope - solve exactly what the issue asks, nothing more
- Test assumptions - run the code before committing
- Resist new dependencies - each one is attack surface and maintenance

## Architecture and Structure

```
algo/
├── main.yml                 # Primary playbook
├── users.yml               # User management playbook
├── server.yml              # Server-specific tasks
├── config.cfg              # Main configuration file
├── pyproject.toml          # Python project configuration and dependencies
├── uv.lock                 # Exact dependency versions lockfile
├── requirements.yml        # Ansible collections
├── roles/                  # Ansible roles
│   ├── common/            # Base system configuration, firewall, hardening
│   ├── wireguard/         # WireGuard VPN setup
│   ├── strongswan/        # IPsec/IKEv2 setup
│   ├── dns/               # DNS configuration (dnscrypt-proxy)
│   └── cloud-*/           # Cloud provider specific roles
├── library/               # Custom Ansible modules
└── tests/unit/            # Python unit tests
```

## Development Workflow

### Quality Gates (MANDATORY)

**All PRs must pass these checks locally before submission.** CI will reject failures:

```bash
# Run the full lint suite (same as CI)
ansible-lint . && yamllint . && ruff check . && shellcheck scripts/*.sh
ansible-playbook main.yml --syntax-check
ansible-playbook users.yml --syntax-check
pytest tests/unit/ -q
```

Common lint issues to fix before submitting:
- YAML files missing `---` document start markers
- GitHub workflows with unquoted `on:` (must be `'on':`)
- Using `ignore_errors: true` instead of `failed_when: false`
- Jinja2 spacing errors (`{{foo}}` should be `{{ foo }}`)
- Missing `mode:` on file/directory tasks

### Design Requirements

When adding or modifying features, verify these before requesting review:

1. **Validate inputs early** - Check for empty lists, missing configs, permission mismatches before expensive operations
2. **Explicit file modes** - Always specify `mode:` on file/directory tasks (never rely on umask)
3. **Fail vs warn** - Permission/security issues should fail; optional features can warn
4. **Actionable errors** - Include fix commands in error messages: `"Run: sudo chown -R $USER configs/"`
5. **Follow existing patterns** - Search codebase first: `rg "when:.*localhost" --type yaml`

### Linting Tools

| Tool | Target | Key Rules |
|------|--------|-----------|
| `ansible-lint` | YAML tasks | Use `failed_when` not `ignore_errors`, add `mode:` to files |
| `yamllint` | All YAML | Document start `---`, quote `'on':` in workflows |
| `ruff` | Python | Line length 120, target Python 3.11 |
| `shellcheck` | Shell scripts | Quote variables, use `set -euo pipefail` |

### Git Workflow

1. Create feature branches from `master`
2. Run all linters before pushing
3. Make atomic commits with clear messages
4. Update PR description with test results

### Self-Review Checklist

Before creating a PR, review your own diff:

- [ ] Did I run all linters locally?
- [ ] Did I search for similar patterns in the codebase?
- [ ] Did I add explicit `mode:` to file/directory tasks?
- [ ] Did I validate inputs before expensive operations?
- [ ] Did I update tests if I changed file paths or behavior?
- [ ] Would a reviewer ask "what happens if X is empty/missing?"

## Ansible Pitfalls

### with_items vs loop

`with_items` auto-flattens lists; `loop` does not. **Never mechanically convert:**

```yaml
# WRONG - treats list as single item, creates file named "['alice', 'bob']"
loop:
  - "{{ users }}"

# CORRECT - iterates over list contents
loop: "{{ users }}"

# CORRECT - combining lists (with_items did this automatically)
loop: "{{ users + [server_name] }}"
```

**Always test loop conversions** - verify the task creates expected files.

### Path Variables

Never include trailing slashes - causes double-slash bugs:

```yaml
# WRONG - creates paths like /etc/ipsec.d//private
ipsec_path: "configs/{{ server }}/ipsec/"

# CORRECT
ipsec_path: "configs/{{ server }}/ipsec"
```

### ignore_errors vs failed_when

```yaml
# WRONG - ansible-lint failure
- name: Clear history
  command: some_command
  ignore_errors: true

# CORRECT - explicit about expected failures
- name: Clear history
  command: some_command
  failed_when: false
```

### changed_when on Read-Only Tasks

Handlers and check commands that don't modify state need `changed_when: false`:

```yaml
- name: Check service status
  command: systemctl status foo
  changed_when: false
```

### Jinja2 Native Mode (Ansible 12+)

Ansible 12 enables `jinja2_native` by default, changing how values are evaluated:

**Boolean conditionals require actual booleans:**
```yaml
# WRONG - string "true" is not boolean
ipv6_support: "{% if ipv6 %}true{% else %}false{% endif %}"

# CORRECT - return actual boolean
ipv6_support: "{{ ipv6 is defined }}"
```

**No nested templates in lookup():**
```yaml
# WRONG - deprecated double-templating
key: "{{ lookup('file', '{{ SSH_keys.public }}') }}"

# CORRECT - pass variable directly
key: "{{ lookup('file', SSH_keys.public) }}"
```

**JSON files need explicit parsing:**
```yaml
# WRONG - returns string in native mode
creds: "{{ lookup('file', 'credentials.json') }}"

# CORRECT - parse JSON explicitly
creds: "{{ lookup('file', 'credentials.json') | from_json }}"
```

**default() doesn't trigger on empty strings:**
```yaml
# WRONG - empty string '' is not undefined
key: "{{ lookup('env', 'AWS_KEY') | default('fallback') }}"

# CORRECT - add true to handle falsy values
key: "{{ lookup('env', 'AWS_KEY') | default('fallback', true) }}"
```

**Complex Jinja loops break in set_fact:**
```yaml
# WRONG - list comprehension fails in native mode
servers: "[{% for s in configs %}{{ s.name }},{% endfor %}]"

# CORRECT - use Ansible loop
servers: "{{ servers | default([]) + [item.name] }}"
loop: "{{ configs }}"
```

**Use tests (not filters) for boolean checks:**
```yaml
# WRONG - filters return transformed data, not booleans
that: my_ip | ansible.utils.ipv4

# CORRECT - tests return native booleans
that: my_ip is ansible.utils.ipv4_address
```

## DNS Architecture

Algo uses a randomly generated IP in 172.16.0.0/12 on the loopback interface (`local_service_ip`) for DNS. This provides consistency across WireGuard and IPsec but requires understanding systemd socket activation.

### Why This Design

- Consistent DNS IP across both VPN protocols
- Survives interface changes and restarts
- Works identically across all cloud providers
- Trade-off: Requires `route_localnet=1` sysctl

### systemd Socket Activation

Ubuntu's dnscrypt-proxy uses socket activation which **completely ignores** the `listen_addresses` config setting. You must configure the socket, not the service:

```ini
# /etc/systemd/system/dnscrypt-proxy.socket.d/10-algo-override.conf
[Socket]
ListenStream=              # Clear defaults first
ListenDatagram=
ListenStream=172.x.x.x:53  # Then set VPN IP
ListenDatagram=172.x.x.x:53
```

Common mistakes:
- Trying to disable/mask the socket (breaks service dependency)
- Only setting ListenStream (need ListenDatagram for UDP)
- Forgetting to restart socket after config changes

### Debugging DNS

Many "routing" issues are actually DNS issues. Start here:

```bash
ss -lnup | grep :53                      # Should show local_service_ip:53
systemctl status dnscrypt-proxy.socket   # Check for config warnings
sysctl net.ipv4.conf.all.route_localnet  # Must be 1
dig @172.x.x.x google.com                # Test resolution
```

For comprehensive diagnostics, see [docs/troubleshooting.md](docs/troubleshooting.md#diagnostic-commands).

## Common Issues

### iptables Backend (nft vs legacy)

Ubuntu 22.04+ defaults to iptables-nft which reorders rules unpredictably. Algo forces iptables-legacy for consistent behavior. Switching backends can break DNS routing that previously worked.

### Multi-homed Systems (DigitalOcean, etc.)

Servers with both public and private IPs on the same interface need explicit output interface for NAT:

```yaml
-o {{ ansible_default_ipv4['interface'] }}
```

Don't overengineer with SNAT - MASQUERADE with interface specification works fine.

### OpenSSL Version Compatibility

OpenSSL 3.x dropped support for legacy algorithms. Add `-legacy` flag conditionally:

```yaml
{{ (openssl_version is version('3', '>=')) | ternary('-legacy', '') }}
```

### IPv6 Endpoint Formatting

WireGuard configs must bracket IPv6 addresses:

```jinja2
{% if ':' in IP %}[{{ IP }}]:{{ port }}{% else %}{{ IP }}:{{ port }}{% endif %}
```

### Jinja2 Templates

Many templates use Ansible-specific filters. Test with `tests/unit/test_template_rendering.py` and mock Ansible filters when testing.

## Time Wasters to Avoid

Lessons learned - don't spend time on these unless absolutely necessary:

1. **Converting MASQUERADE to SNAT** - MASQUERADE works fine for Algo's use case
2. **Fighting systemd socket activation** - Configure it properly instead of disabling
3. **Debugging NAT before checking DNS** - Most "routing" issues are DNS issues
4. **Complex IPsec policy matching** - Keep NAT rules simple
5. **Testing on existing servers** - Always test on fresh deployments
6. **Interface-specific route_localnet** - WireGuard interface doesn't exist until service starts
7. **DNAT for loopback addresses** - Packets to local IPs don't traverse PREROUTING

## What to Avoid

- **Speculative features** - Don't add "might be useful" functionality. Open an issue instead.
- **New dependencies without justification** - Vanilla Ansible/Python can do most things.
- **Bundling unrelated fixes** - One PR, one purpose. Separate issues get separate PRs.
- **Assuming behavior** - If converting `with_items` to `loop`, test that it still works. If adding a firewall rule, verify packets flow.
- **Configuration options** - Don't add flags unless users actively need them. Each option doubles testing surface.
- **Undocumented workarounds** - When working around broken upstream modules, file an issue and add a comment linking to it. Future maintainers need to know why workarounds exist.

## Writing Effective Tests

When writing tests, **verify your test actually detects the failure case** (mutation testing approach):

1. Write the test for the bug you're preventing
2. Temporarily introduce the bug to verify the test fails
3. Fix the bug and verify the test passes
4. Document what specific issue the test prevents

```python
def test_regression_openssl_inline_comments():
    """Tests that we detect inline comments in Jinja2 expressions."""
    # This pattern SHOULD fail (has inline comments)
    problematic = "{{ ['DNS:' + id,  # comment ] }}"
    assert not validate(problematic), "Should detect inline comments"

    # This pattern SHOULD pass (no inline comments)
    fixed = "{{ ['DNS:' + id] }}"
    assert validate(fixed), "Should pass without comments"
```

## Quick Reference

### Local Development Setup

```bash
uv sync
uv run ansible-galaxy install -r requirements.yml
ansible-playbook main.yml -e "provider=local"
```

### Common Commands

```bash
# Add/update users
ansible-playbook users.yml -e "server=SERVER_NAME"

# Update dependencies
uv lock && pytest tests/unit/ -q

# Debug deployment
ansible-playbook main.yml -vvv
```

### Key Directories

- `configs/` - Generated client configurations
- `roles/*/tasks/` - Main task files
- `roles/*/templates/` - Jinja2 templates
- `library/` - Custom Ansible modules (add to `mock_modules` in `.ansible-lint`)

## Non-Interactive Deployment

All `pause:` prompts in `input.yml` and provider roles skip when their
variable is pre-defined via `-e` or environment variables. This enables
fully headless deployment for CI, agents, and scripted workflows.
See [docs/deploy-from-ansible.md](docs/deploy-from-ansible.md) for
full human-facing documentation.

### Core variables

These bypass the main prompts in `input.yml`:

| Variable | Type | Default | Purpose |
|----------|------|---------|---------|
| `provider` | string | *(prompt)* | Provider alias (e.g., `digitalocean`, `ec2`, `local`) |
| `server_name` | string | `algo` | VPN server name |
| `ondemand_cellular` | bool | `false` | iOS/macOS Connect On Demand for cellular |
| `ondemand_wifi` | bool | `false` | iOS/macOS Connect On Demand for Wi-Fi |
| `ondemand_wifi_exclude` | string | *(none)* | Comma-separated trusted Wi-Fi networks |
| `store_pki` | bool | `false` | Retain PKI keys (needed to add users later) |
| `dns_adblocking` | bool | `false` | Enable DNS ad blocking |
| `ssh_tunneling` | bool | `false` | Per-user SSH tunnel accounts |

### Provider credentials

| Provider | `-e` variables | Env var fallbacks |
|----------|---------------|-------------------|
| `digitalocean` | `do_token`, `region` | `DO_API_TOKEN` |
| `ec2` | `aws_access_key`, `aws_secret_key`, `region` | `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` (also reads `~/.aws/credentials`) |
| `lightsail` | `aws_access_key`, `aws_secret_key`, `region` | `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` |
| `azure` | `azure_secret`, `azure_tenant`, `azure_client_id`, `azure_subscription_id`, `region` | `AZURE_SECRET`, `AZURE_TENANT`, `AZURE_CLIENT_ID`, `AZURE_SUBSCRIPTION_ID` |
| `gce` | `gce_credentials_file`, `region` | `GCE_CREDENTIALS_FILE_PATH` |
| `hetzner` | `hcloud_token`, `region` | `HCLOUD_TOKEN` |
| `vultr` | `vultr_config`, `region` | `VULTR_API_CONFIG` |
| `scaleway` | `scaleway_token`, `scaleway_org_id`, `region` | `SCW_TOKEN`, `SCW_DEFAULT_ORGANIZATION_ID` |
| `linode` | `linode_token`, `region` | `LINODE_API_TOKEN` |
| `cloudstack` | `cs_key`, `cs_secret`, `cs_url`, `region` | `CLOUDSTACK_KEY`, `CLOUDSTACK_SECRET`, `CLOUDSTACK_ENDPOINT` |
| `openstack` | `region` | `OS_AUTH_URL` (source your `openrc.sh`) |
| `local` | `server`, `endpoint`, `local_install_confirmed` | *(none)* |

### Minimal examples

```bash
# DigitalOcean — fully headless
ansible-playbook main.yml -e \
  "provider=digitalocean
   server_name=algo
   region=nyc3
   do_token=YOUR_TOKEN
   ondemand_cellular=false
   ondemand_wifi=false
   dns_adblocking=false
   ssh_tunneling=false
   store_pki=false"

# Local — for CI/testing
ansible-playbook main.yml -e \
  "provider=local
   server=localhost
   endpoint=10.0.0.1
   local_install_confirmed=true
   ondemand_cellular=false
   ondemand_wifi=false
   dns_adblocking=false
   ssh_tunneling=false"
```

### Updating users non-interactively

```bash
ansible-playbook users.yml -e "server=YOUR_SERVER ca_password=YOUR_CA_PASS"
```

The `server` variable bypasses the server selection prompt.
`ca_password` is only required when IPsec is enabled.

## Security Considerations

- **Never expose secrets** - No passwords/keys in commits
- **CVE Response** - Update immediately when security issues found
- **Least Privilege** - Minimal permissions, dropped capabilities
- **Secure Defaults** - Strong crypto (secp384r1), no logging, strict firewall

## Platform Support

- **Primary OS**: Ubuntu 22.04/24.04 LTS
- **Secondary**: Debian 11/12
- **Architectures**: x86_64 and ARM64
- **Testing tip**: DigitalOcean droplets have both public and private IPs on eth0, making them good test cases for multi-IP NAT scenarios
