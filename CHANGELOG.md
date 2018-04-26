## 30 Apr 2018
### Added
- WireGuard support

### Removed
- Android StrongSwan profiles

### Release notes
- StrongSwan profiles for Android are deprecated now. Use WireGuard

## 25 Apr 2018
### Added
- DNScrypt-proxy added
- Switched to CloudFlare DNS-over-HTTPS by default

## 19 Apr 2018
### Added
- IPv6 in subjectAltName of the certificates. This allows connecting to the Algo instance via the main IPv6 address

### Fixed
- IPv6 DNS addresses were not passing to the client

### Release notes
- In order to use the IPv6 address as the connection endpoint you need to [reinit](https://github.com/trailofbits/algo/blob/master/config.cfg#L14) the PKI and [reconfigure](https://github.com/trailofbits/algo#configure-the-vpn-clients) your devices with new certificates.
