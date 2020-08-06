## 1.2 [(Unreleased)](https://github.com/trailofbits/algo/tree/HEAD)

### Added
- New provider CloudStack added [\#1420](https://github.com/trailofbits/algo/pull/1420)
- Support for Ubuntu 20.04 [\#1782](https://github.com/trailofbits/algo/pull/1782)
- Allow WireGuard to listen on port 53 [\#1594](https://github.com/trailofbits/algo/pull/1594)
- Introducing Makefile [\#1553](https://github.com/trailofbits/algo/pull/1553)
- Option to unblock SMB and Netbios [\#1558](https://github.com/trailofbits/algo/pull/1558)
- Allow OnDemand to be toggled later [\#1557](https://github.com/trailofbits/algo/pull/1557)
- New provider Hetzner added [\#1549](https://github.com/trailofbits/algo/pull/1549)
- Alternative Ingress IP [\#1605](https://github.com/trailofbits/algo/pull/1605)

### Fixes
- WSL private SSH key permissions [\#1584](https://github.com/trailofbits/algo/pull/1584)
- Scaleway instance creating issue [\#1549](https://github.com/trailofbits/algo/pull/1549)

### Changed
- Discontinue use of the WireGuard PPA [\#1855](https://github.com/trailofbits/algo/pull/1855)
- SSH changes [\#1636](https://github.com/trailofbits/algo/pull/1636)
  - Default port is set to `4160` and can be changed in the config
  - SSH user for every cloud provider is `algo`
- EC2: enable EBS encryption by default [\#1556](https://github.com/trailofbits/algo/pull/1556)
- Upgrades [\#1549](https://github.com/trailofbits/algo/pull/1549)
  - Python 3
  - Ansible 2.9 [\#1777](https://github.com/trailofbits/algo/pull/1777)
  
 ### Breaking changes
  - Python virtual environment moved to .env [\#1549](https://github.com/trailofbits/algo/pull/1549)


## 1.1 [(Jul 31, 2019)](https://github.com/trailofbits/algo/releases/tag/v1.1)

### Removed
- IKEv2 for Windows is now deleted, use Wireguard [\#1493](https://github.com/trailofbits/algo/issues/1493)

### Added
- Tmpfs for key generation [\#145](https://github.com/trailofbits/algo/issues/145)
- Randomly generated pre-shared keys for WireGuard [\#1465](https://github.com/trailofbits/algo/pull/1465) ([elreydetoda](https://github.com/elreydetoda))
- Support for Ubuntu 19.04 [\#1405](https://github.com/trailofbits/algo/pull/1405) ([jackivanov](https://github.com/jackivanov))
- AWS support for existing EIP [\#1292](https://github.com/trailofbits/algo/pull/1292) ([statik](https://github.com/statik))
- Script to support cloud-init and local easy deploy [\#1366](https://github.com/trailofbits/algo/pull/1366) ([jackivanov](https://github.com/jackivanov))
- Automatically create cloud firewall rules for installs onto Vultr [\#1400](https://github.com/trailofbits/algo/pull/1400) ([TC1977](https://github.com/TC1977))
- Randomly generated IP address for the local dns resolver [\#1429](https://github.com/trailofbits/algo/pull/1429) ([jackivanov](https://github.com/jackivanov))
- Update users: add server pick-list [\#1441](https://github.com/trailofbits/algo/pull/1441) ([TC1977](https://github.com/TC1977))
- Additional testing [\#213](https://github.com/trailofbits/algo/issues/213)
- Add IPv6 support to DNS [\#1425](https://github.com/trailofbits/algo/pull/1425) ([shapiro125](https://github.com/shapiro125))
- Additional p12 with the CA cert included [\#1403](https://github.com/trailofbits/algo/pull/1403) ([jackivanov](https://github.com/jackivanov))

### Fixed
- Fixes error in 10-algo-lo100.network [\#1369](https://github.com/trailofbits/algo/pull/1369) ([adamluk](https://github.com/adamluk))
- Error message is missing for some roles [\#1364](https://github.com/trailofbits/algo/issues/1364)
- DNS leak in Linux/Wireguard when LAN gateway/DNS is 172.16.0.1 [\#1422](https://github.com/trailofbits/algo/issues/1422)
- Installation error after \#1397 [\#1409](https://github.com/trailofbits/algo/issues/1409)
- EC2 encrypted images bug [\#1528](https://github.com/trailofbits/algo/issues/1528)

### Changed
- Upgrade Ansible to 2.7.12 [\#1536](https://github.com/trailofbits/algo/pull/1536)
- DNSmasq removed, and the DNS adblocking functionality has been moved to the dnscrypt-proxy
- Azure: moved to the Standard_B1S image size
- Refactoring, Linting and additional tests [\#1397](https://github.com/trailofbits/algo/pull/1397) ([jackivanov](https://github.com/jackivanov))
- Scaleway modules [\#1410](https://github.com/trailofbits/algo/pull/1410) ([jackivanov](https://github.com/jackivanov))
- Use VULTR_API_CONFIG variable if set [\#1374](https://github.com/trailofbits/algo/pull/1374) ([davidemyers](https://github.com/davidemyers))
- Simplify Apple Profile Configuration Template [\#1033](https://github.com/trailofbits/algo/pull/1033) ([faf0](https://github.com/faf0))
- Include roles as separate tasks [\#1365](https://github.com/trailofbits/algo/pull/1365) ([jackivanov](https://github.com/jackivanov))

## 1.0 [(Mar 19, 2019)](https://github.com/trailofbits/algo/releases/tag/v1.0)

### Added 
- Tagged releases and changelog [\#724](https://github.com/trailofbits/algo/issues/724)
- Add support for custom domain names [\#759](https://github.com/trailofbits/algo/issues/759)

### Fixed
- Set the name shown to the user \(client\) to be the server name specified in the install script [\#491](https://github.com/trailofbits/algo/issues/491)
- AGPLv3 change [\#1351](https://github.com/trailofbits/algo/pull/1351)
- Migrate to python3 [\#1024](https://github.com/trailofbits/algo/issues/1024)
- Reorganize the project around ipsec + wireguard [\#1330](https://github.com/trailofbits/algo/issues/1330)
- Configuration folder reorganization [\#1330](https://github.com/trailofbits/algo/issues/1330)
- Remove WireGuard KeepAlive and include as an option in config [\#1251](https://github.com/trailofbits/algo/issues/1251)
- Dnscrypt-proxy no longer works after reboot [\#1356](https://github.com/trailofbits/algo/issues/1356)

## 20 Oct 2018
### Added
- AWS Lightsail

## 7 Sep 2018
### Changed
- Azure: Deployment via Azure Resource Manager

## 27 Aug 2018
### Changed
- Large refactor to support Ansible 2.5. [Details](https://github.com/trailofbits/algo/pull/976)
- Add a new cloud provider - Vultr

### Upgrade notes
- If any problems encountered follow the [instructions](https://github.com/trailofbits/algo#deploy-the-algo-server) from scratch
- You can't update users on your old servers with the new code. Use the old code before this release or rebuild the server from scratch
- Update AWS IAM permissions for your user as per [issue](https://github.com/trailofbits/algo/issues/1079#issuecomment-416577599)

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
