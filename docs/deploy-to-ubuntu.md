# Local Installation

**IMPORTANT**: Algo is designed to create a dedicated VPN server. There is no uninstallation option. Installing Algo on an existing server may break existing services, especially since firewall rules will be overwritten. See [AlgoVPN and Firewalls](/docs/firewalls.md) for details.

## Requirements

Algo currently supports **Ubuntu 22.04 LTS only**. Your target server must be running an unmodified installation of Ubuntu 22.04.

## Installation

You can install Algo on an existing Ubuntu server instead of creating a new cloud instance. This is called a **local** installation. If you're new to Algo or Linux, cloud deployment is easier.

1. Follow the normal Algo installation instructions
2. When prompted, choose: `Install to existing Ubuntu latest LTS server (for advanced users)`
3. The target can be:
   - The same system where you installed Algo (requires `sudo ./algo`)
   - A remote Ubuntu server accessible via SSH without password prompts (use `ssh-agent`)

For local installation on the same machine, you must run:
```bash
sudo ./algo
```

## Road Warrior Setup

A "road warrior" setup lets you securely access your home network and its resources when traveling. This involves installing Algo on a server within your home LAN.

**Network Configuration:**
- Forward the necessary ports from your router to the Algo server (see [firewall documentation](/docs/firewalls.md#external-firewall))

**Algo Configuration** (edit `config.cfg` before deployment):
- Set `BetweenClients_DROP` to `false` (allows VPN clients to reach your LAN)
- Consider setting `block_smb` and `block_netbios` to `false` (enables SMB/NetBIOS traffic)
- For local DNS resolution (e.g., Pi-hole), set `dns_encryption` to `false` and update `dns_servers` to your local DNS server IP
