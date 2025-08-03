# Privacy Enhancements Role

This Ansible role implements additional privacy enhancements for Algo VPN to minimize server-side traces of VPN usage and reduce log retention. These measures help protect user privacy while maintaining system security.

## Features

### 1. Aggressive Log Rotation
- Configures shorter log retention periods (default: 7 days)
- Implements more frequent log rotation
- Compresses rotated logs to save space
- Automatically cleans up old log files

### 2. History Clearing
- Clears bash/shell history after deployment
- Disables persistent command history for system users
- Clears temporary files and caches
- Sets up automatic history clearing on user logout

### 3. VPN Log Filtering
- Filters out VPN connection logs from rsyslog
- Excludes WireGuard and StrongSwan messages from persistent storage
- Filters kernel messages related to VPN traffic
- Optional filtering of authentication logs (use with caution)

### 4. Automatic Cleanup
- Daily/weekly/monthly cleanup of old logs and temporary files
- Package cache cleaning
- Configurable retention policies
- Optional shutdown cleanup for extreme privacy

### 5. Advanced Privacy Settings
- Reduced kernel log verbosity
- Disabled successful SSH connection logging (optional)
- Volatile systemd journal storage
- Privacy monitoring script

## Configuration

All privacy settings are configured in `config.cfg` under the "Privacy Enhancements" section:

```yaml
# Enable/disable all privacy enhancements
privacy_enhancements_enabled: true

# Log rotation settings
privacy_log_rotation:
  max_age: 7              # Days to keep logs
  max_size: 10            # Max size per log file (MB)
  rotate_count: 3         # Number of rotated files to keep
  compress: true          # Compress rotated logs
  daily_rotation: true    # Force daily rotation

# History clearing
privacy_history_clearing:
  clear_bash_history: true
  clear_system_history: true
  disable_service_history: true

# Log filtering
privacy_log_filtering:
  exclude_vpn_logs: true
  exclude_auth_logs: false    # Use with caution
  filter_kernel_vpn_logs: true

# Automatic cleanup
privacy_auto_cleanup:
  enabled: true
  frequency: "daily"          # daily, weekly, monthly
  temp_files_max_age: 1
  clean_package_cache: true

# Advanced settings
privacy_advanced:
  disable_ssh_success_logs: false
  reduce_kernel_verbosity: true
  clear_logs_on_shutdown: false  # Extreme measure
```

## Security Considerations

### Safe Settings (Default)
- `exclude_vpn_logs: true` - Safe, only filters VPN-specific messages
- `clear_bash_history: true` - Safe, improves privacy without affecting security
- `reduce_kernel_verbosity: true` - Safe, reduces noise in logs

### Use With Caution
- `exclude_auth_logs: true` - Reduces security logging, makes incident investigation harder
- `disable_ssh_success_logs: true` - Removes audit trail for successful connections
- `clear_logs_on_shutdown: true` - Extreme measure, makes debugging very difficult

## Files Created

### Configuration Files
- `/etc/logrotate.d/99-privacy-enhanced` - Main log rotation config
- `/etc/logrotate.d/99-auth-privacy` - Auth log rotation
- `/etc/logrotate.d/99-kern-privacy` - Kernel log rotation
- `/etc/rsyslog.d/49-privacy-vpn-filter.conf` - VPN log filtering
- `/etc/rsyslog.d/48-privacy-kernel-filter.conf` - Kernel log filtering
- `/etc/rsyslog.d/47-privacy-auth-filter.conf` - Auth log filtering (optional)
- `/etc/rsyslog.d/46-privacy-ssh-filter.conf` - SSH log filtering (optional)
- `/etc/rsyslog.d/45-privacy-minimal.conf` - Minimal logging config

### Scripts
- `/usr/local/bin/privacy-auto-cleanup.sh` - Automatic cleanup script
- `/usr/local/bin/privacy-log-cleanup.sh` - Initial log cleanup
- `/usr/local/bin/privacy-monitor.sh` - Privacy status monitoring
- `/etc/bash.bash_logout` - History clearing on logout

### Systemd Services
- `/etc/systemd/system/privacy-shutdown-cleanup.service` - Shutdown cleanup (optional)

## Usage

### Enable Privacy Enhancements
Privacy enhancements are enabled by default. To disable them:

```yaml
privacy_enhancements_enabled: false
```

### Run Specific Privacy Tasks
You can run specific privacy components using tags:

```bash
# Run only log rotation setup
ansible-playbook server.yml --tags privacy-logs

# Run only history clearing
ansible-playbook server.yml --tags privacy-history

# Run only log filtering
ansible-playbook server.yml --tags privacy-filtering

# Run only cleanup tasks
ansible-playbook server.yml --tags privacy-cleanup

# Run all privacy enhancements
ansible-playbook server.yml --tags privacy
```

### Monitor Privacy Status
Check the status of privacy enhancements:

```bash
sudo /usr/local/bin/privacy-monitor.sh
```

### Manual Cleanup
Run manual cleanup:

```bash
sudo /usr/local/bin/privacy-auto-cleanup.sh
```

## Debugging

If you need to debug VPN issues, temporarily disable privacy enhancements:

1. Set `privacy_enhancements_enabled: false` in `config.cfg`
2. Re-run the deployment: `./algo`
3. Debug your issues with full logging
4. Re-enable privacy enhancements when done

Alternatively, disable specific features:
- Set `exclude_vpn_logs: false` to see VPN connection logs
- Set `reduce_kernel_verbosity: false` for full kernel logging
- Check `/var/log/privacy-cleanup.log` for cleanup operation logs

## Impact on System

### Positive Effects
- Improved user privacy
- Reduced disk usage from logs
- Faster log searches
- Reduced attack surface

### Potential Drawbacks
- Limited debugging information
- Shorter audit trail
- May complicate troubleshooting
- Could hide security incidents

## Compatibility

- **Ubuntu 22.04**: Fully supported
- **FreeBSD**: Limited support (log rotation and history clearing only)
- **Other distributions**: May require adaptation

## Best Practices

1. **Start Conservative**: Use default settings initially
2. **Test Thoroughly**: Verify VPN functionality after enabling privacy features
3. **Monitor Logs**: Check that essential security logs are still being captured
4. **Document Changes**: Keep track of privacy settings for troubleshooting
5. **Regular Reviews**: Periodically review privacy settings and their effectiveness

## Privacy vs. Security Balance

This role aims to balance privacy with security by:
- Keeping security-critical logs (authentication failures, system errors)
- Filtering only VPN-specific operational logs
- Providing granular control over what gets filtered
- Maintaining essential audit trails while reducing VPN usage traces

For maximum privacy, consider running your own log analysis before enabling aggressive filtering options.