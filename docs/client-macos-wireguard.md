# Using MacOS as a Client with WireGuard

## Install WireGuard

To connect to your Algo VPN using [WireGuard](https://www.wireguard.com) from MacOS

```
# Install the wireguard-go userspace driver
brew install wireguard-tools
```

## Locate the Config File

The Algo-generated config files for WireGuard are named `configs/<ip_address>/wireguard/<username>.conf` on the system where you ran `./algo`. One file was generated for each of the users you added to `config.cfg` before you ran `./algo`. Each Linux and Android client you connect to your Algo VPN must use a different WireGuard config file. Choose one of these files and copy it to your device.

## Configure WireGuard

Finally, install the config file on your client as `/usr/local/etc/wireguard/wg0.conf` and start WireGuard:

```
# Install the config file to the WireGuard configuration directory on your MacOS device
mkdir /usr/local/etc/wireguard/
cp <username>.conf /usr/local/etc/wireguard/wg0.conf

# Start the WireGuard VPN:
sudo wg-quick up wg0

# Verify the connection to the Algo VPN:
wg

# See that your client is using the IP address of your Algo VPN:
curl ipv4.icanhazip.com
```
