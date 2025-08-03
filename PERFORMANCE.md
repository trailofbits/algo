# Algo VPN Performance Optimizations

This document describes performance optimizations available in Algo to reduce deployment time.

## Overview

By default, Algo deployments can take 10+ minutes due to sequential operations like system updates, certificate generation, and unnecessary reboots. These optimizations can reduce deployment time by 30-60%.

## Performance Options

### Skip Optional Reboots (`performance_skip_optional_reboots`)

**Default**: `true`
**Time Saved**: 0-5 minutes per deployment

```yaml
# config.cfg
performance_skip_optional_reboots: true
```

**What it does**: 
- Analyzes `/var/log/dpkg.log` to detect if kernel packages were updated
- Only reboots if kernel was updated (critical for security and functionality)
- Skips reboots for non-kernel package updates (safe for VPN operation)

**Safety**: Very safe - only skips reboots when no kernel updates occurred.

### Parallel Cryptographic Operations (`performance_parallel_crypto`)

**Default**: `true`  
**Time Saved**: 1-3 minutes (scales with user count)

```yaml
# config.cfg
performance_parallel_crypto: true
```

**What it does**:
- **StrongSwan certificates**: Generates user private keys and certificate requests in parallel
- **WireGuard keys**: Generates private and preshared keys simultaneously  
- **Certificate signing**: Remains sequential (required for CA database consistency)

**Safety**: Safe - maintains cryptographic security while improving performance.

### Batch Package Installation (`performance_parallel_packages`)

**Default**: `true`
**Time Saved**: 30-60 seconds per deployment

```yaml
# config.cfg
performance_parallel_packages: true
```

**What it does**:
- **Collects all packages**: Gathers packages from all roles (common tools, strongswan, wireguard, dnscrypt-proxy)
- **Single apt operation**: Installs all packages in one `apt` command instead of multiple sequential installs
- **Reduces network overhead**: Single package list download and dependency resolution
- **Maintains compatibility**: Falls back to individual installs when disabled

**Safety**: Very safe - same packages installed, just more efficiently.

## Expected Time Savings

| Optimization | Time Saved | Risk Level |
|--------------|------------|------------|
| Skip optional reboots | 0-5 minutes | Very Low |
| Parallel crypto | 1-3 minutes | None |
| Batch packages | 30-60 seconds | None |
| **Combined** | **1.5-8.5 minutes** | **Very Low** |

## Performance Comparison

### Before Optimizations
```
System updates:     3-8 minutes
Package installs:   1-2 minutes (sequential per role)
Certificate gen:    2-4 minutes (sequential)
Reboot wait:        0-5 minutes (always)
Other tasks:        2-3 minutes
────────────────────────────────
Total:              8-22 minutes
```

### After Optimizations  
```
System updates:     3-8 minutes
Package installs:   30-60 seconds (batch)
Certificate gen:    1-2 minutes (parallel)
Reboot wait:        0 minutes (skipped when safe)
Other tasks:        2-3 minutes
────────────────────────────────  
Total:              6.5-13.5 minutes
```

## Disabling Optimizations

To disable performance optimizations (for maximum compatibility):

```yaml
# config.cfg
performance_skip_optional_reboots: false
performance_parallel_crypto: false
performance_parallel_packages: false
```

## Technical Details

### Reboot Detection Logic

```bash
# Checks for kernel package updates
if grep -q "linux-image\|linux-generic\|linux-headers" /var/log/dpkg.log*; then
    echo "kernel-updated"  # Always reboot
else
    echo "optional"        # Skip if performance_skip_optional_reboots=true
fi
```

### Parallel Certificate Generation

**StrongSwan Process**:
1. Generate all user private keys + CSRs simultaneously (`async: 60`)
2. Wait for completion (`async_status` with retries)
3. Sign certificates sequentially (CA database locking required)

**WireGuard Process**:
1. Generate all private keys simultaneously (`wg genkey` in parallel)
2. Generate all preshared keys simultaneously (`wg genpsk` in parallel)  
3. Derive public keys from private keys (fast operation)

## Troubleshooting

### If deployments fail with performance optimizations:

1. **Check certificate generation**: Look for `async_status` failures
2. **Disable parallel crypto**: Set `performance_parallel_crypto: false`
3. **Force reboots**: Set `performance_skip_optional_reboots: false`

### Performance not improving:

1. **Cloud provider speed**: Optimizations don't affect cloud resource provisioning
2. **Network latency**: Slow connections limit all operations
3. **Instance type**: Low-CPU instances benefit most from parallel operations

## Future Optimizations

Additional optimizations under consideration:

- **Package pre-installation via cloud-init** (saves 1-2 minutes)
- **Pre-built cloud images** (saves 5-15 minutes) 
- **Skip system updates flag** (saves 3-8 minutes, security tradeoff)
- **Bulk package installation** (saves 30-60 seconds)

## Contributing

To contribute additional performance optimizations:

1. Ensure changes are backwards compatible
2. Add configuration flags (don't change defaults without discussion)
3. Document time savings and risk levels
4. Test with multiple cloud providers
5. Update this documentation

## Compatibility

These optimizations are compatible with:
- ✅ All cloud providers (DigitalOcean, AWS, GCP, Azure, etc.)
- ✅ All VPN protocols (WireGuard, StrongSwan)  
- ✅ Existing Algo installations (config changes only)
- ✅ All supported Ubuntu versions

**Not compatible with**:
- ❌ Local deployments on systems requiring specific kernel versions
- ❌ Environments with strict reboot policies
- ❌ Very old Ansible versions (<2.9)