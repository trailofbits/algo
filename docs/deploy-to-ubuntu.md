# Local Installation

**PLEASE NOTE**: Algo is intended for use to create a _dedicated_ VPN server. No uninstallation option is provided. If you install Algo on an existing server any existing services might break. In particular, the firewall rules will be overwritten. See [AlgoVPN and Firewalls](/docs/firewalls.md) for more information.

------

## Outbound VPN Server

You can use Algo to configure a pre-existing server as an AlgoVPN rather than using it to create and configure a new server on a supported cloud provider. This is referred to as a **local** installation rather than a **cloud** deployment. If you're new to Algo or unfamiliar with Linux you'll find a cloud deployment to be easier.

To perform a local installation, install the Algo scripts following the normal installation instructions, then choose:

```
Install to existing Ubuntu latest LTS server (for more advanced users)
```

Make sure your target server is running an unmodified copy of the operating system version specified. The target can be the same system where you've installed the Algo scripts, or a remote system that you are able to access as root via SSH without needing to enter the SSH key passphrase (such as when using `ssh-agent`).

## Inbound VPN Server (also called "Road Warrior" setup)

Some may find it useful to set up an Algo server on an Ubuntu box on your home LAN, with the intention of being able to securely access your LAN and any resources on it when you're traveling elsewhere (the ["road warrior" setup](https://en.wikipedia.org/wiki/Road_warrior_(computing))). A few tips if you're doing so:

- Make sure you forward any [relevant incoming ports](/docs/firewalls.md#external-firewall) to the Algo server from your router;
- Change `BetweenClients_DROP` in `config.cfg` to `false`, and also consider changing `block_smb` and `block_netbios` to `false`;
- If you want to use a DNS server on your LAN to resolve local domain names properly (e.g. a Pi-hole), set the `dns_encryption` flag in `config.cfg` to `false`, and change `dns_servers` to the local DNS server IP (i.e. `192.168.1.2`).
