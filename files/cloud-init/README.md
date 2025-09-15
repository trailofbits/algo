# Cloud-Init Files - Critical Format Requirements

## ⚠️ CRITICAL WARNING ⚠️

The files in this directory have **STRICT FORMAT REQUIREMENTS** that must not be changed by linters or automated formatting tools.

## Cloud-Config Header Format

The first line of `base.yml` **MUST** be exactly:
```
#cloud-config
```

### ❌ DO NOT CHANGE TO:
- `# cloud-config` (space after #) - **BREAKS CLOUD-INIT PARSING**
- Add YAML document start `---` - **NOT ALLOWED IN CLOUD-INIT**

### Why This Matters

Cloud-init's YAML parser expects the exact string `#cloud-config` as the first line. Any deviation causes:

1. **Complete parsing failure** - All directives are skipped
2. **SSH configuration not applied** - Servers remain on port 22 instead of 4160
3. **Deployment timeouts** - Ansible cannot connect to configure the VPN
4. **DigitalOcean specific impact** - Other providers may be more tolerant

## Historical Context

- **Working**: All versions before PR #14775 (August 2025)
- **Broken**: PR #14775 "Apply ansible-lint improvements" added space by mistake
- **Fixed**: PR #14801 restored correct format + added protections

See GitHub issue #14800 for full technical details.

## Linter Configuration

These files are **excluded** from:
- `yamllint` (`.yamllint` config)
- `ansible-lint` (`.ansible-lint` config)

This prevents automated tools from "fixing" the format and breaking deployments.

## Template Variables

The cloud-init files use Jinja2 templating:
- `{{ ssh_port }}` - Configured SSH port (typically 4160)
- `{{ lookup('file', '{{ SSH_keys.public }}') }}` - SSH public key

## Editing Guidelines

1. **Never** run automated formatters on these files
2. **Test immediately** after any changes with real deployments
3. **Check yamllint warnings** are expected (missing space in comment, missing ---)
4. **Verify first line** remains exactly `#cloud-config`

## References

- [Cloud-init documentation](https://cloudinit.readthedocs.io/)
- [Cloud-config examples](https://cloudinit.readthedocs.io/en/latest/reference/examples.html)
- [GitHub Issue #14800](https://github.com/trailofbits/algo/issues/14800)
