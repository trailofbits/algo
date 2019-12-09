# Using Ubuntu as a Client with WireGuard

## Install WireGuard

To connect to your AlgoVPN using [WireGuard](https://www.wireguard.com) from Ubuntu, first install WireGuard:

```shell
# Ubuntu 19.04 and earlier:
# Add the WireGuard repository
sudo add-apt-repository ppa:wireguard/wireguard

# Ubuntu 17.10 and earlier:
# Update the list of available packages
sudo apt update

# Install the tools and kernel module:
sudo apt install wireguard openresolv
```

For installation on other Linux distributions, see the [Installation](https://www.wireguard.com/install/) page on the WireGuard site.

## Locate the Config File

The Algo-generated config files for WireGuard are named `configs/<ip_address>/wireguard/<username>.conf` on the system where you ran `./algo`. One file was generated for each of the users you added to `config.cfg`. Each WireGuard client you connect to your AlgoVPN must use a different config file. Choose one of these files and copy it to your Linux client.

## Configure WireGuard

Finally, install the config file on your client as `/etc/wireguard/wg0.conf` and start WireGuard:

```shell
# Install the config file to the WireGuard configuration directory on your
# Linux client:
sudo install -o root -g root -m 600 <username>.conf /etc/wireguard/wg0.conf

# Start the WireGuard VPN:
sudo systemctl start wg-quick@wg0

# Check that it started properly:
sudo systemctl status wg-quick@wg0

# Verify the connection to the AlgoVPN:
sudo wg

# See that your client is using the IP address of your AlgoVPN:
curl ipv4.icanhazip.com

# Optionally configure the connection to come up at boot time:
sudo systemctl enable wg-quick@wg0
```

If your Linux distribution does not use `systemd` you can bring up WireGuard with `sudo wg-quick up wg0`.
