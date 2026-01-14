# Windows Client Setup

This guide will help you set up your Windows device to connect to your Algo VPN server.

## Supported Versions

- Windows 10 (all editions)
- Windows 11 (all editions)
- Windows Server 2016 and later

## WireGuard Setup (Recommended)

WireGuard is the recommended VPN protocol for Windows clients due to its simplicity and performance.

### Installation

1. Download and install the official [WireGuard client for Windows](https://www.wireguard.com/install/)
2. Locate your configuration file: `configs/<server-ip>/wireguard/<username>.conf`
3. In the WireGuard application, click "Import tunnel(s) from file"
4. Select your `.conf` file and import it
5. Click "Activate" to connect to your VPN

### Alternative Import Methods

- **QR Code**: If you have access to the QR code (`wireguard/<username>.png`), you can scan it using a mobile device first, then export the configuration
- **Manual Entry**: You can create a new empty tunnel and paste the contents of your `.conf` file

## IPsec/IKEv2 Setup (Legacy)

While Algo supports IPsec/IKEv2, it requires PowerShell scripts for Windows setup. WireGuard is strongly recommended instead.

If you must use IPsec:
1. Locate the PowerShell setup script in your configs directory
2. Run PowerShell as Administrator
3. Execute the setup script
4. The VPN connection will appear in Settings → Network & Internet → VPN

## Troubleshooting

### "The parameter is incorrect" Error

This is a common error that occurs when trying to connect. See the [troubleshooting guide](troubleshooting.md#windows-the-parameter-is-incorrect-error-when-connecting) for the solution.

### Connection Issues

1. **Check Windows Firewall**: Ensure Windows Firewall isn't blocking the VPN connection
2. **Verify Server Address**: Make sure the server IP/domain in your configuration is correct
3. **Check Date/Time**: Ensure your system date and time are correct
4. **Disable Other VPNs**: Disconnect from any other VPN services before connecting

### WireGuard Specific Issues

- **DNS Not Working**: Check if "Block untunneled traffic (kill-switch)" is enabled in tunnel settings
- **Slow Performance**: Try reducing the MTU in the tunnel configuration (default is 1420)
- **Can't Import Config**: Ensure the configuration file has a `.conf` extension

### Performance Optimization

1. **Use WireGuard**: It's significantly faster than IPsec on Windows
2. **Close Unnecessary Apps**: Some antivirus or firewall software can slow down VPN connections
3. **Check Network Adapter**: Update your network adapter drivers to the latest version

## Advanced Configuration

### Split Tunneling

To exclude certain traffic from the VPN:
1. Edit your WireGuard configuration file
2. Modify the `AllowedIPs` line to exclude specific networks
3. For example, to exclude local network: Remove `0.0.0.0/0` and add specific routes

### Automatic Connection

To connect automatically:
1. Open WireGuard
2. Select your tunnel
3. Edit → Uncheck "On-demand activation"
4. Windows will maintain the connection automatically

### Multiple Servers

You can import multiple `.conf` files for different Algo servers. Give each a descriptive name to distinguish them.

## Security Notes

- Keep your configuration files secure - they contain your private keys
- Don't share your configuration with others
- Each user should have their own unique configuration
- Regularly update your WireGuard client for security patches

## Need More Help?

- Check the main [troubleshooting guide](troubleshooting.md)
- Review [WireGuard documentation](https://www.wireguard.com/quickstart/)
- [Create a discussion](https://github.com/trailofbits/algo/discussions) for help
