# OpenWrt Router as WireGuard Client

This guide explains how to configure an OpenWrt router as a WireGuard VPN client, allowing all devices connected to your network to route traffic through your Algo VPN automatically. This setup is ideal for devices that don't support VPN natively (smart TVs, IoT devices, game consoles) or when you want seamless VPN access for all network clients.

## Use Cases

- Connect devices without native VPN support (smart TVs, gaming consoles, IoT devices)
- Automatically route all connected devices through the VPN
- Create a secure connection when traveling with multiple devices
- Configure VPN once at the router level instead of per-device

## Prerequisites

You'll need an OpenWrt-compatible router with sufficient RAM (minimum 64MB recommended) and OpenWrt 23.05 or later installed. Your Algo VPN server must be deployed and running, and you'll need the WireGuard configuration file from your Algo deployment.

Ensure your router's LAN subnet doesn't conflict with upstream networks. The default OpenWrt IP is `192.168.1.1` - change to `192.168.2.1` if conflicts exist.

This configuration has been verified on TP-Link TL-WR1043ND and TP-Link Archer C20i AC750 with OpenWrt 23.05+. For compatibility with other devices, check the [OpenWrt Table of Hardware](https://openwrt.org/toh/start).

## Install Required Packages

### Web Interface Method

1. Access your router's web interface (typically `http://192.168.1.1`)
2. Login with your credentials (default: username `root`, no password)
3. Navigate to System → Software
4. Click "Update lists" to refresh the package database
5. Search for and install these packages:
   - `wireguard-tools`
   - `kmod-wireguard` 
   - `luci-app-wireguard`
   - `wireguard`
   - `kmod-crypto-sha256`
   - `kmod-crypto-sha1`
   - `kmod-crypto-md5`
6. Restart the router after installation completes

### SSH Method

1. SSH into your router: `ssh root@192.168.1.1`
2. Update the package list:
   ```bash
   opkg update
   ```
3. Install required packages:
   ```bash
   opkg install wireguard-tools kmod-wireguard luci-app-wireguard wireguard kmod-crypto-sha256 kmod-crypto-sha1 kmod-crypto-md5
   ```
4. Reboot the router:
   ```bash
   reboot
   ```

## Locate Your WireGuard Configuration

Before proceeding, locate your WireGuard configuration file from your Algo deployment. This file is typically located at:
```
configs/<server_ip>/wireguard/<username>.conf
```

Your configuration file should look similar to:
```ini
[Interface]
PrivateKey = <your_private_key>
Address = 10.49.0.2/16
DNS = 172.16.0.1

[Peer]
PublicKey = <server_public_key>
PresharedKey = <preshared_key>
AllowedIPs = 0.0.0.0/0, ::/0
Endpoint = <server_ip>:51820
PersistentKeepalive = 25
```

## Configure WireGuard Interface

1. In the OpenWrt web interface, navigate to Network → Interfaces
2. Click "Add new interface..."
3. Set the name to `AlgoVPN` (or your preferred name) and select "WireGuard VPN" as the protocol
4. Click "Create interface"

In the General Settings tab:
- Check "Bring up on boot"
- Enter your private key from the Algo config file
- Add your IP address from the Algo config file (e.g., `10.49.0.2/16`)

Switch to the Peers tab and click "Add peer":
- Description: `Algo Server`
- Public Key: Copy from the `[Peer]` section of your config
- Preshared Key: Copy from the `[Peer]` section of your config
- Allowed IPs: `0.0.0.0/0, ::/0` (routes all traffic through VPN)
- Route Allowed IPs: Check this box
- Endpoint Host: Extract the IP address from the `Endpoint` line
- Endpoint Port: Extract the port from the `Endpoint` line (typically `51820`)
- Persistent Keep Alive: `25`

Click "Save & Apply".

## Configure Firewall Rules

1. Navigate to Network → Firewall
2. Click "Add" to create a new zone
3. Configure the firewall zone:
   - Name: `vpn`
   - Input: `Reject`
   - Output: `Accept`
   - Forward: `Reject`
   - Masquerading: Check this box
   - MSS clamping: Check this box
   - Covered networks: Select your WireGuard interface (`AlgoVPN`)

4. In the Inter-Zone Forwarding section:
   - Allow forward from source zones: Select `lan`
   - Allow forward to destination zones: Leave unspecified

5. Click "Save & Apply"
6. Reboot your router to ensure all changes take effect

## Verification and Testing

Navigate to Network → Interfaces and verify your WireGuard interface shows as "Connected" with a green status. Check that it has received the correct IP address.

From a device connected to your router, visit https://whatismyipaddress.com/. Your public IP should match your Algo VPN server's IP address. Test DNS resolution to ensure it's working through the VPN.

For command line verification, SSH into your router and check:
```bash
# Check interface status
wg show

# Check routing table
ip route

# Test connectivity
ping 8.8.8.8
```

## Configuration File Reference

Your OpenWrt network configuration (`/etc/config/network`) should include sections similar to:

```uci
config interface 'AlgoVPN'
    option proto 'wireguard'
    list addresses '10.49.0.2/16'
    option private_key '<your_private_key>'

config wireguard_AlgoVPN
    option public_key '<server_public_key>'
    option preshared_key '<preshared_key>'
    option route_allowed_ips '1'
    list allowed_ips '0.0.0.0/0'
    list allowed_ips '::/0'
    option endpoint_host '<server_ip>'
    option endpoint_port '51820'
    option persistent_keepalive '25'
```

## Troubleshooting

If the interface won't connect, verify all keys are correctly copied with no extra spaces or line breaks. Check that your Algo server is running and accessible, and confirm the endpoint IP and port are correct.

If you have no internet access after connecting, verify firewall rules allow forwarding from LAN to VPN zone. Check that masquerading is enabled on the VPN zone and ensure MSS clamping is enabled.

If some websites don't work, try disabling MSS clamping temporarily to test. Verify DNS is working by testing `nslookup google.com` and check that IPv6 is properly configured if used.

For DNS resolution issues, configure custom DNS servers in Network → DHCP and DNS. Consider using your Algo server's DNS (typically `172.16.0.1`).

Check system logs for WireGuard-related errors:
```bash
# View system logs
logread | grep -i wireguard

# Check kernel messages
dmesg | grep -i wireguard
```

## Advanced Configuration

For split tunneling (routing only specific traffic through the VPN), change "Allowed IPs" in the peer configuration to specific subnets and add custom routing rules for desired traffic.

If your Algo server supports IPv6, add the IPv6 address to your interface configuration and include `::/0` in "Allowed IPs" for the peer.

For optimal privacy, configure your router to use your Algo server's DNS by navigating to Network → DHCP and DNS and adding your Algo DNS server IP (typically `172.16.0.1`) to the DNS forwardings.

## Security Notes

Store your private keys securely and never share them. Keep OpenWrt and packages updated for security patches. Regularly check VPN connectivity to ensure ongoing protection, and save your configuration before making changes.

This configuration routes ALL traffic from your router through the VPN. If you need selective routing or have specific requirements, consider consulting the [OpenWrt WireGuard documentation](https://openwrt.org/docs/guide-user/services/vpn/wireguard/start) for advanced configurations.