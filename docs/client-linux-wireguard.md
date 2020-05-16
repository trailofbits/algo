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

## Using a DNS Search Domain

As of the `v1.0.20200510` release of `wireguard-tools` WireGuard supports setting a DNS search domain. In your `wg0.conf` file a non-numeric entry on the `DNS` line will be used as a search domain. For example this:
```
DNS =  172.27.153.31, fd00::b:991f, mydomain.com
```
will cause your `/etc/resolv.conf` to contain:
```
search mydomain.com
nameserver 172.27.153.31
nameserver fd00::b:991f
```
If you're using the version of WireGuard included with Ubuntu as of 19.10 it might be from before this feature was added. To use the latest version of WireGuard add the PPA repository as shown above.

Note that using the PPA repository on Ubuntu 20.04 LTS instead of the WireGuard modules shipped in the kernel package may cause the installation of about 40 additional packages in order to compile the kernel module.
