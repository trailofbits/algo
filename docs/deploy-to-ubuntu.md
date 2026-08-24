# Local Installation

**IMPORTANT**: Algo is designed to create a dedicated VPN server. There is no uninstallation option. Installing Algo on an existing server may break existing services, especially since firewall rules will be overwritten. See [AlgoVPN and Firewalls](/docs/firewalls.md) for details.

## Requirements

Algo supports **Ubuntu 22.04 LTS and Ubuntu 24.04 LTS**. Your target server must be running an unmodified installation of one of these releases. Other distributions and Ubuntu releases, including Ubuntu 26.04, are rejected before Ubuntu-specific configuration begins.

`ubuntu_version` in `config.cfg` selects the server release. It accepts only `"22.04"` or `"24.04"`. Ubuntu 22.04 remains the default transition release; Ubuntu 24.04 must not be described as the primary/default cloud target until credentialed create/configure/destroy canaries pass.

## Provider image selector status

No live provider deployment was performed for this support matrix. "Public selector" means only that the provider's public native catalog or documentation exposes the selector; it does **not** mean Algo provisioning was verified with provider credentials.

| Provider | 22.04 | 24.04 | Evidence/status |
| --- | --- | --- | --- |
| DigitalOcean | Public selector | Public selector | Provider [Droplet image catalog](https://docs.digitalocean.com/products/droplets/details/images/) lists both API slugs. |
| Amazon EC2 | Public lookup | Public lookup | Algo queries Canonical owner `099720109477` by release-specific AMI name, following Ubuntu's [AWS image discovery guidance](https://documentation.ubuntu.com/aws/aws-how-to/instances/find-ubuntu-images/). No AMI ID is guessed or fixed. |
| Google Compute Engine | Public family | Public family | Uses Google-maintained `ubuntu-os-cloud` [public image families](https://cloud.google.com/compute/docs/images/os-details#ubuntu_lts). |
| Scaleway | Public label | Public label | Provider CLI/API documentation identifies `ubuntu_jammy` and [`ubuntu_noble`](https://www.scaleway.com/en/docs/instances/api-cli/creating-managing-instances-with-cliv2/) marketplace labels; the role resolves the zone-local image ID from the Marketplace API. |
| Hetzner Cloud | Public image name | Public image name | Uses system-image names (`ubuntu-22.04`, `ubuntu-24.04`), not guessed numeric IDs; see the [Cloud image API](https://docs.hetzner.cloud/reference/cloud#resources-images). |
| Vultr | Public catalog name | Public catalog name | The unauthenticated provider-native [`/v2/os`](https://api.vultr.com/v2/os) catalog lists both names. |
| Linode | Public image | Public image | The unauthenticated public image API exposes [`linode/ubuntu22.04`](https://api.linode.com/v4/images/linode/ubuntu22.04) and [`linode/ubuntu24.04`](https://api.linode.com/v4/images/linode/ubuntu24.04). |
| OpenStack | Existing 22.04 only | **Unverified/unsupported** | Image names are deployment-specific; there is no universal 24.04 selector. Configure and test the target cloud catalog before advertising support. |
| CloudStack | Existing 22.04 only | **Unverified/unsupported** | Templates are cloud/zone-specific; there is no universal 24.04 selector. |
| Azure | Existing 22.04 only | **Unverified/unsupported in this change** | Azure was explicitly excluded from the 24.04 selector work. |
| Amazon Lightsail | Existing 22.04 only | **Unverified/unsupported in this change** | Lightsail was explicitly excluded from the 24.04 selector work. |
| Existing/local server | Accepted after fact validation | Accepted after fact validation | No provider image is created; the common role verifies the actual distribution and version before configuration. |

## Installation

You can install Algo on an existing Ubuntu server instead of creating a new cloud instance. This is called a **local** installation. If you're new to Algo or Linux, cloud deployment is easier.

1. Follow the normal Algo installation instructions
2. When prompted, choose: `Install to existing Ubuntu 22.04 or 24.04 LTS server (for advanced users)`
3. The target can be:
   - The same system where you installed Algo (requires `sudo ./algo`)
   - A remote Ubuntu server accessible via SSH without password prompts (use `ssh-agent`)

For local installation on the same machine, you must run:
```bash
sudo ./algo
```

## Confirmation Prompt

Local installation displays a warning and requires you to type `yes` to proceed. This ensures you understand that Algo will modify firewall rules and system settings, and that there is no uninstall option.

For automated deployments or CI/CD pipelines, skip the confirmation with:
```bash
ansible-playbook main.yml -e "provider=local local_install_confirmed=true server=localhost endpoint=YOUR_IP"
```

Only use `local_install_confirmed=true` when you have already taken a backup and understand the risks.

## Road Warrior Setup

A "road warrior" setup lets you securely access your home network and its resources when traveling. This involves installing Algo on a server within your home LAN.

**Network Configuration:**
- Forward the necessary ports from your router to the Algo server (see [firewall documentation](/docs/firewalls.md#external-firewall))

**Algo Configuration** (edit `config.cfg` before deployment):
- Set `BetweenClients_DROP` to `false` (allows VPN clients to reach your LAN)
- Consider setting `block_smb` and `block_netbios` to `false` (enables SMB/NetBIOS traffic)
- For local DNS resolution (e.g., Pi-hole), set `dns_encryption` to `false` and update `dns_servers` to your local DNS server IP
