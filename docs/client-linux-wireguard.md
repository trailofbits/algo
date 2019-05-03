# Using Ubuntu Server as a Client with WireGuard

## Install WireGuard

To connect to your AlgoVPN using [WireGuard](https://www.wireguard.com) from Ubuntu Server, first install WireGuard:

```shell
# Add the WireGuard repository:
sudo add-apt-repository ppa:wireguard/wireguard

# Update the list of available packages (not necessary on Bionic or later):
sudo apt update 

# Install the tools and kernel module:
sudo apt install wireguard
```

For installation on other Linux distributions, see the [Installation](https://www.wireguard.com/install/) page on the WireGuard site.

## Locate the Config File

The Algo-generated config files for WireGuard are named `configs/<ip_address>/wireguard/<username>.conf` on the system where you ran `./algo`. One file was generated for each of the users you added to `config.cfg`. Each WireGuard client you connect to your AlgoVPN must use a different config file. Choose one of these files and copy it to your Linux client.

## Configure DNS

### Ubuntu 18.04 (Bionic)

If your client is running Bionic (or another Linux that uses `systemd-resolved` for DNS but does not have `resolvectl` or `resolvconf` installed) you should first edit the config file. Comment out the line that begins with `DNS =` and replace it with:
```
PostUp = systemd-resolve -i %i --set-dns=172.16.0.1 --set-domain=~.
```
Use the IP address shown on the `DNS =` line (for most, this will be `172.16.0.1`). If the `DNS =` line contains multiple IP addresses, use multiple  `--set-dns=` options.

### Ubuntu 18.10 (Cosmic) or 19.04 (Disco)

If your client is running Cosmic or Disco (or another Linux that uses `systemd-resolved` for DNS and has `resolvectl` but *not* `resolvconf` installed) you can either edit the config file as shown above for Bionic or run the following command once:

```
sudo ln -s /usr/bin/resolvectl /usr/bin/resolvconf
```

### Other Linux Distributions

On other Linux distributions you might need to install the `openresolv` package.

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
