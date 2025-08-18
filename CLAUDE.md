# CLAUDE.md - LLM Guidance for Algo VPN

This document provides essential context and guidance for LLMs working on the Algo VPN codebase. It captures important learnings, patterns, and best practices discovered through extensive work with this project.

## Project Overview

Algo is an Ansible-based tool that sets up a personal VPN in the cloud. It's designed to be:
- **Security-focused**: Creates hardened VPN servers with minimal attack surface
- **Easy to use**: Automated deployment with sensible defaults
- **Multi-platform**: Supports various cloud providers and operating systems
- **Privacy-preserving**: No logging, minimal data retention

### Core Technologies
- **VPN Protocols**: WireGuard (preferred) and IPsec/IKEv2
- **Configuration Management**: Ansible (currently v9.x)
- **Languages**: Python, YAML, Shell, Jinja2 templates
- **Supported Providers**: AWS, Azure, DigitalOcean, GCP, Vultr, Hetzner, local deployment

## Architecture and Structure

### Directory Layout
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
│   ├── common/            # Base system configuration
│   ├── wireguard/         # WireGuard VPN setup
│   ├── strongswan/        # IPsec/IKEv2 setup
│   ├── dns/               # DNS configuration (dnsmasq, dnscrypt)
│   ├── ssh_tunneling/     # SSH tunnel setup
│   └── cloud-*/           # Cloud provider specific roles
├── library/               # Custom Ansible modules
├── playbooks/             # Supporting playbooks
└── tests/                 # Test suite
    └── unit/             # Python unit tests
```

### Key Roles
- **common**: Firewall rules, system hardening, package management
- **wireguard**: WireGuard server/client configuration
- **strongswan**: IPsec server setup with certificate generation
- **dns**: DNS encryption and ad blocking
- **cloud-\***: Provider-specific instance creation

## Critical Dependencies and Version Management

### Current Versions (MUST maintain compatibility)
```
ansible==11.8.0     # Stay current to get latest security, performance and bugfixes
jinja2~=3.1.6      # Security fix for CVE-2025-27516
netaddr==1.3.0     # Network address manipulation
```

### Version Update Guidelines
1. **Be Conservative**: Prefer minor version bumps over major ones
2. **Security First**: Always prioritize security updates (CVEs)
3. **Test Thoroughly**: Run all tests before updating
4. **Document Changes**: Explain why each update is necessary

### Ansible Collections
Currently unpinned in `requirements.yml`, but key ones include:
- `community.general`
- `ansible.posix`
- `openstack.cloud`

## Development Practices

### Code Style and Linting

#### Python (ruff)
```toml
# pyproject.toml configuration
[tool.ruff]
target-version = "py311"
line-length = 120

[tool.ruff.lint]
select = ["E", "W", "F", "I", "B", "C4", "UP"]
```

#### YAML (yamllint)
- Document start markers (`---`) required
- No trailing spaces
- Newline at end of file
- Quote `'on':` in GitHub workflows (truthy value)

#### Shell Scripts (shellcheck)
- Quote all variables: `"${var}"`
- Use `set -euo pipefail` for safety

#### PowerShell Scripts (PSScriptAnalyzer)
- Use approved verbs (Get-, Set-, New-, etc.)
- Avoid positional parameters in functions
- Use proper error handling with try/catch
- **Note**: Algo's PowerShell script is a WSL wrapper since Ansible doesn't run natively on Windows

#### Ansible (ansible-lint)
- Many warnings are suppressed in `.ansible-lint`
- Focus on errors, not warnings
- Common suppressions: `name[missing]`, `risky-file-permissions`

#### Documentation Style
- Avoid excessive header nesting (prefer 2-3 levels maximum)
- Don't overuse bold formatting in lists - use sparingly for emphasis only
- Write flowing paragraphs instead of choppy bullet-heavy sections
- Keep formatting clean and readable - prefer natural text over visual noise
- Use numbered lists for procedures, simple bullets for feature lists
- Example: "Navigate to Network → Interfaces" not "**Navigate** to **Network** → **Interfaces**"

### Git Workflow
1. Create feature branches from `master`
2. Make atomic commits with clear messages
3. Run all linters before pushing
4. Update PR description with test results
5. Squash commits if requested

### Testing Requirements

Before pushing any changes:
```bash
# Python tests
pytest tests/unit/ -v

# Ansible syntax
ansible-playbook main.yml --syntax-check
ansible-playbook users.yml --syntax-check

# Linters
ansible-lint
yamllint .
ruff check .
shellcheck *.sh

# PowerShell (if available)
pwsh -Command "Invoke-ScriptAnalyzer -Path ./algo.ps1"
```

### Writing Effective Tests - Mutation Testing Approach

When writing tests, **always verify that your test actually detects the failure case**. This is a form of lightweight mutation testing that ensures tests add real value:

1. **Write the test for the bug/issue you're preventing**
2. **Temporarily introduce the bug** to verify the test fails
3. **Fix the bug** and verify the test passes
4. **Document what specific issue the test prevents**

Example from our codebase:
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

This practice ensures:
- Tests aren't just checking happy paths
- Tests will actually catch regressions
- The test's purpose is clear to future maintainers
- We avoid false confidence from tests that always pass

## Common Issues and Solutions

### 1. Ansible-lint "name[missing]" Warnings
- Added to skip_list in `.ansible-lint`
- Too many tasks to fix immediately (113+)
- Focus on new code having proper names

### 2. dnscrypt-proxy Service Failures
**Problem:** "Unit dnscrypt-proxy.socket is masked" or service won't start
- The service has `Requires=dnscrypt-proxy.socket` dependency
- Masking the socket prevents the service from starting
- **Solution:** Configure socket properly instead of fighting it (see systemd section above)

### 3. DNS Not Accessible to VPN Clients
**Symptoms:** VPN connects but no internet access
- First check: `sudo ss -ulnp | grep :53` on the server
- If only showing 127.0.0.53 or 127.0.2.1, socket activation is misconfigured
- Check firewall allows VPN subnets: `-A INPUT -s {{ subnets }} -d {{ local_service_ip }}`
- **Never** allow DNS from all sources (0.0.0.0/0) - security risk!

### 4. Multi-homed Systems and NAT
**DigitalOcean and other providers with multiple IPs:**
- Servers may have both public and private IPs on same interface
- MASQUERADE needs output interface: `-o {{ ansible_default_ipv4['interface'] }}`
- Don't overengineer with SNAT - MASQUERADE with interface works fine
- Use `alternative_ingress_ip` option only when truly needed

### 5. Jinja2 Template Complexity
- Many templates use Ansible-specific filters
- Test templates with `tests/unit/test_template_rendering.py`
- Mock Ansible filters when testing

### 6. OpenSSL Version Compatibility
```yaml
# Check version and use appropriate flags
{{ (openssl_version is version('3', '>=')) | ternary('-legacy', '') }}
```

### 7. IPv6 Endpoint Formatting
- WireGuard configs must bracket IPv6 addresses
- Template logic: `{% if ':' in IP %}[{{ IP }}]:{{ port }}{% else %}{{ IP }}:{{ port }}{% endif %}`

## Security Considerations

### Always Priority One
- **Never expose secrets**: No passwords/keys in commits
- **CVE Response**: Update immediately when security issues found
- **Least Privilege**: Minimal permissions, dropped capabilities
- **Secure Defaults**: Strong crypto, no logging, firewall rules

### Certificate Management
- Elliptic curve cryptography (secp384r1)
- Proper CA password handling
- Certificate revocation support
- Secure storage in `/etc/ipsec.d/`

### Network Security
- Strict firewall rules (iptables/ip6tables)
- No IP forwarding except for VPN
- DNS leak protection
- Kill switch implementation

## Platform Support

### Operating Systems
- **Primary**: Ubuntu 20.04/22.04 LTS
- **Secondary**: Debian 11/12
- **Clients**: Windows, macOS, iOS, Android, Linux

### Cloud Providers
Each has specific requirements:
- **AWS**: Requires boto3, specific AMI IDs
- **Azure**: Complex networking setup
- **DigitalOcean**: Simple API, good for testing (watch for multiple IPs on eth0)
- **Local**: KVM/Docker for development

**Testing Note:** DigitalOcean droplets often have both public and private IPs on the same interface, making them excellent test cases for multi-IP scenarios and NAT issues.

### Architecture Considerations
- Support both x86_64 and ARM64
- Some providers have limited ARM support
- Performance varies by instance type

## CI/CD Pipeline

### GitHub Actions Workflows
1. **lint.yml**: Runs ansible-lint on all pushes
2. **main.yml**: Tests cloud provider configurations
3. **smart-tests.yml**: Selective test running based on changes
4. **integration-tests.yml**: Full deployment tests (currently disabled)

### Test Categories
- **Unit Tests**: Python-based, test logic and templates
- **Syntax Checks**: Ansible playbook validation
- **Linting**: Code quality enforcement
- **Integration**: Full deployment testing (needs work)

## Maintenance Guidelines

### Dependency Updates
1. Check for security vulnerabilities monthly
2. Update conservatively (minor versions)
3. Test on multiple platforms
4. Document in PR why updates are needed

### Issue Triage
- Security issues: Priority 1
- Broken functionality: Priority 2
- Feature requests: Priority 3
- Check issues for duplicates

### Pull Request Standards
- Clear description of changes
- Test results included
- Linter compliance
- Conservative approach

### Time Wasters to Avoid (Lessons Learned)
**Don't spend time on these unless absolutely necessary:**
1. **Converting MASQUERADE to SNAT** - MASQUERADE works fine for Algo's use case
2. **Fighting systemd socket activation** - Configure it properly instead
3. **Debugging NAT before checking DNS** - Most "routing" issues are DNS issues
4. **Complex IPsec policy matching** - Keep NAT rules simple
5. **Testing on existing servers** - Always test on fresh deployments
6. **Adding `-m policy --pol none`** - This breaks NAT, don't use it

## Working with Algo

### Local Development Setup
```bash
# Install dependencies
uv sync
uv run ansible-galaxy install -r requirements.yml

# Run local deployment
ansible-playbook main.yml -e "provider=local"
```

### Common Tasks

#### Adding a New User
```bash
ansible-playbook users.yml -e "server=SERVER_NAME"
```

#### Updating Dependencies
1. Create a new branch
2. Update pyproject.toml conservatively
3. Run `uv lock` to update lockfile
4. Run all tests
5. Document security fixes

#### Debugging Deployment Issues
1. Check `ansible-playbook -vvv` output
2. Verify cloud provider credentials
3. Check firewall rules
4. Review generated configs in `configs/`

### Troubleshooting VPN Connectivity

#### "VPN connects but can't route traffic" - Check in this order:
1. **DNS first** - `sudo ss -ulnp | grep :53` - Is dnscrypt-proxy listening on VPN IPs?
2. **Packet counters** - `sudo iptables -L FORWARD -v -n | grep -E '10.49|10.48'` - Are packets reaching the firewall?
3. **NAT counters** - `sudo iptables -t nat -L POSTROUTING -v -n` - Is NAT happening?
4. **Service status** - `sudo systemctl status dnscrypt-proxy` - Is the DNS service running?

**Important:** Most "routing" issues are actually DNS issues. Always check DNS first.

#### systemd and dnscrypt-proxy
- Ubuntu's dnscrypt-proxy package uses socket activation by default
- The default socket listens on 127.0.2.1:53, NOT the VPN service IPs
- Work WITH systemd, not against it:
  ```yaml
  # Create socket override at /etc/systemd/system/dnscrypt-proxy.socket.d/override.conf
  [Socket]
  ListenStream=  # Clear defaults
  ListenStream=172.x.x.x:53  # Add VPN IP
  ```
- Use empty `listen_addresses = []` in dnscrypt-proxy.toml when using socket activation
- **Never** use `TriggeredBy=` in systemd units (it's not a valid directive)
- Don't mask sockets that services depend on - just disable them

## Important Context for LLMs

### What Makes Algo Special
- **Simplicity**: One command to deploy
- **Security**: Hardened by default
- **No Bloat**: Minimal dependencies
- **Privacy**: No telemetry or logging

### User Expectations
- It should "just work"
- Security is non-negotiable
- Backwards compatibility matters
- Clear error messages

### Common User Profiles
1. **Privacy Advocates**: Want secure communications
2. **Travelers**: Need reliable VPN access
3. **Small Teams**: Shared VPN for remote work
4. **Developers**: Testing and development

### Maintenance Philosophy
- Stability over features
- Security over convenience
- Clarity over cleverness
- Test everything

## Final Notes

When working on Algo:
1. **Think Security First**: Every change should maintain or improve security
2. **Test Thoroughly**: Multiple platforms, both VPN types
3. **Document Clearly**: Users may not be technical
4. **Be Conservative**: This is critical infrastructure
5. **Respect Privacy**: No tracking, minimal logging

Remember: People trust Algo with their privacy and security. Every line of code matters.