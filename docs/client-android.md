# Android client setup

## Installation via profiles

1. [Install the WireGuard VPN Client](https://play.google.com/store/apps/details?id=com.wireguard.android).
2. Add the configuration to your device, one of two ways:
    * via QR code (more secure):
        * Run `qrencode -t ansiutf8 < wireguard/{username}.conf`
        * Open the WireGuard app and add a connection QR code.
    * Manually:
        * Copy `wireguard/{username}.conf` to your phone's internal storage.
        * Open the WireGuard app and add a connection using your AlgoVPN configuration file.
