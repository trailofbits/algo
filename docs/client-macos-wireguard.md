# MacOS WireGuard Client Setup

The WireGuard macOS app is unavailable for older operating systems. Please update your operating system if you can. If you are on a macOS High Sierra (10.13) or earlier, then you can still use WireGuard via their userspace drivers via the process detailed below.

## Install WireGuard

Install the wireguard-go userspace driver:

```
brew install wireguard-tools
```

## Locate the Config File

Algo generates a WireGuard configuration file, `wireguard/<username>.conf`, and a QR code, `wireguard/<username>.png`, for each user defined in `config.cfg`. Find the configuration file and copy it to your device if you don't already have it.

Note that each client you use to connect to Algo VPN must have a unique WireGuard config.

## Configure WireGuard

You'll need to copy the appropriate WireGuard configuration file into a location where the userspace driver can find it. After it is in the right place, start the VPN, and verify connectivity.

```
# Copy the config file to the WireGuard configuration directory on your macOS device
mkdir /usr/local/etc/wireguard/
cp <username>.conf /usr/local/etc/wireguard/wg0.conf

# Start the WireGuard VPN
sudo wg-quick up wg0

# Verify the connection to the Algo VPN
wg

# See that your client is using the IP address of your Algo VPN:
curl ipv4.icanhazip.com
```
