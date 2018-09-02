# Using Ubuntu Server as a Client with WireGuard

## Install WireGuard

To connect to your Algo VPN using [WireGuard](https://www.wireguard.com) from an Ubuntu Server 16.04 (Xenial) or 18.04 (Bionic) client, first install WireGuard on the client:

```shell
# Add the WireGuard repository:
sudo add-apt-repository ppa:wireguard/wireguard

# Update the list of available packages (not necessary on Bionic):
sudo apt update 

# Install the tools and kernel module:
sudo apt install wireguard
```

(For installation on other Linux distributions, see the [Installation](https://www.wireguard.com/install/) page on the WireGuard site.)

## Locate the Config File

The Algo-generated config files for WireGuard are named `configs/<ip_address>/wireguard/<username>.conf` on the system where you ran `./algo`. One file was generated for each of the users you added to `config.cfg` before you ran `./algo`. Each Linux and Android client you connect to your Algo VPN must use a different WireGuard config file. Choose one of these files and copy it to your Linux client.

If your client is running Bionic (or another Linux that uses `systemd-resolved` for DNS) you should first edit the config file. Comment out the line that begins with `DNS =` and replace it with:
```
PostUp = systemd-resolve -i %i --set-dns=172.16.0.1 --set-domain=~.
```
Use the IP address shown on the `DNS =` line (for most, this will be `172.16.0.1`). If the `DNS =` line contains multiple IP addresses, use multiple  `--set-dns=` options.

## Configure WireGuard

Finally, install the config file on your client as `/etc/wireguard/wg0.conf` and start WireGuard:

```shell
# Install the config file to the WireGuard configuration directory on your
# Bionic or Xenial client:
sudo install -o root -g root -m 600 <username>.conf /etc/wireguard/wg0.conf

# Start the WireGuard VPN:
sudo systemctl start wg-quick@wg0

# Check that it started properly:
sudo systemctl status wg-quick@wg0

# Verify the connection to the Algo VPN:
sudo wg

# See that your client is using the IP address of your Algo VPN:
curl ipv4.icanhazip.com

# Optionally configure the connection to come up at boot time:
sudo systemctl enable wg-quick@wg0
```

(If your Linux distribution does not use `systemd`, you can bring up WireGuard with `sudo wg-quick up wg0`).
