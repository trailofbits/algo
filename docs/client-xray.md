# VLESS+Reality Client Setup Guide

VLESS with XTLS-Reality is a stealth VPN protocol that makes your traffic indistinguishable from regular HTTPS traffic. It's effective in networks where WireGuard and other VPN protocols are blocked.

## Generated Configuration Files

After deployment, client configuration files are located in:

```
configs/<server_ip>/xray/
├── <username>.json     # Full xray client config
├── <username>.txt      # VLESS share link
└── <username>.png      # QR code for mobile apps
```

## Client Applications

### iOS/macOS

**Shadowrocket** (Recommended)
1. Open Shadowrocket
2. Tap the QR code icon in the top-left corner
3. Scan the QR code from `<username>.png`
4. Or copy the VLESS link from `<username>.txt` and paste it

**Streisand**
1. Open Streisand
2. Tap "+" to add a new server
3. Select "Scan QR Code" or "Import from Clipboard"
4. Use the provided QR code or VLESS link

### Android

**v2rayNG** (Recommended)
1. Install from [Google Play](https://play.google.com/store/apps/details?id=com.v2ray.ang) or [GitHub](https://github.com/2dust/v2rayNG)
2. Tap "+" button → "Import config from Clipboard"
3. Paste the VLESS link from `<username>.txt`
4. Or use the QR code scanner

**NekoBox**
1. Install from [GitHub](https://github.com/MatsuriDayo/NekoBoxForAndroid)
2. Tap "+" → "Import from Clipboard"
3. Paste the VLESS link

### Windows

**v2rayN** (Recommended)
1. Download from [GitHub](https://github.com/2dust/v2rayN)
2. Extract and run `v2rayN.exe`
3. Right-click tray icon → "Import from clipboard"
4. Paste the VLESS link

**Nekoray**
1. Download from [GitHub](https://github.com/MatsuriDayo/nekoray)
2. Server → Add Profile from Clipboard
3. Paste the VLESS link

### Linux

**v2rayA** (Web UI)
1. Install v2rayA following [official docs](https://v2raya.org/)
2. Open web interface (default: http://localhost:2017)
3. Import → Paste VLESS link

**Nekoray**
1. Download from [GitHub](https://github.com/MatsuriDayo/nekoray)
2. Extract and run
3. Server → Add Profile from Clipboard

**Command Line (xray-core)**
1. Install xray-core
2. Copy `<username>.json` to `/etc/xray/config.json`
3. Start service: `sudo systemctl start xray`

## Manual Configuration

If you need to configure manually, use these parameters from your `<username>.txt` file:

| Parameter | Description |
|-----------|-------------|
| Protocol | VLESS |
| Address | Server IP |
| Port | 443 |
| UUID | Your unique user ID |
| Flow | xtls-rprx-vision |
| Security | reality |
| SNI | Configured destination domain |
| Fingerprint | chrome |
| Public Key | Reality public key |
| Short ID | Reality short ID |

## VLESS Link Format

```
vless://UUID@SERVER:443?encryption=none&flow=xtls-rprx-vision&security=reality&sni=DOMAIN&fp=chrome&pbk=PUBLIC_KEY&sid=SHORT_ID&type=tcp#NAME
```

## Troubleshooting

### Connection fails immediately
- Verify server IP and port are correct
- Check if port 443 is open on the server
- Ensure the VLESS link was copied completely

### Connection drops after a few seconds
- Try a different Reality destination domain in `config.cfg`
- Some domains work better in certain regions

### Slow speeds
- VLESS+Reality has minimal overhead, similar to WireGuard
- Check your network connection quality
- Try different client applications

### QR code not scanning
- Ensure good lighting and camera focus
- Try copying the text link from `.txt` file instead

## Security Notes

- Keep your UUID and configuration private
- Each user has a unique UUID
- Sharing configurations allows others to use your server quota
- Reality protocol does not require you to own the destination domain

## Comparison with WireGuard

| Feature | WireGuard | VLESS+Reality |
|---------|-----------|---------------|
| Speed | Excellent | Excellent |
| Stealth | Poor (easily detected) | Excellent |
| Setup | Very simple | Simple |
| Blocked by DPI | Yes, commonly | No |
| Battery usage | Low | Low |
| Protocol | UDP | TCP |

Use WireGuard when it works, VLESS+Reality when WireGuard is blocked.
