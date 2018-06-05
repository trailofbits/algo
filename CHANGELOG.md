## 04 Jun 2018
### Changed
- Switched to [new cipher suite](https://github.com/trailofbits/algo/issues/981)

## 24 May 2018
### Changed
- Switched to Ubuntu 18.04

### Removed
- Lightsail support until they have Ubuntu 18.04

### Fixed
- Scaleway API paginagion

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
