# Ansible Roles

## Required roles

* **Common**
  * Installs several required packages and software updates, then reboots if necessary
  * Configures network interfaces, and enables packet forwarding on them
  * Configures IPtables to block traffic that might pose a risk to VPN users, such as [SMB/CIFS](https://medium.com/@ValdikSS/deanonymizing-windows-users-and-capturing-microsoft-and-vpn-accounts-f7e53fe73834)
  * Enables [unattended-upgrades](https://help.ubuntu.com/community/AutomaticSecurityUpdates) to ensure available patches are always applied
  * Modify features like core dumps, kernel parameters, and SUID binaries to limit possible attacks
  * Enhances SSH with modern ciphers and seccomp, and restricts access to old or unwanted features like X11 forwarding and SFTP
* **Strongswan**
  * Installs [strongSwan](https://www.strongswan.org/), enables AppArmor, limits CPU and memory access, and drops user privileges
  * Builds a Certificate Authority (CA) with [easy-rsa-ipsec](https://github.com/ValdikSS/easy-rsa-ipsec) and creates one client certificate per user
  * Bundles the appropriate certificates into Apple mobileconfig profiles and Powershell scripts for each user
* **Wireguard**
  * Installs a [Wireguard](https://www.wireguard.com/) server, with a script to have it start at the time of server startup, and automatic checks for upgrades
  * Creates wireguard.conf files for Linux clients as well as QR codes for Apple/Android clients
  
Note that you have the option to deploy an Algo server without either Wireguard or Strongswan by editing the `ipsec_enabled` line and/or `wireguard_enabled` line in the `config.cfg` file.

## Optional roles

* **DNS-based Adblocking**
  * Installs the [dnsmasq](http://www.thekelleys.org.uk/dnsmasq/doc.html) local resolver with a blacklist for advertising domains
  * Constrains dnsmasq with AppArmor and cgroups CPU and memory limitations
* **DNS encryption**
  * Installs [dnscrypt-proxy](https://github.com/jedisct1/dnscrypt-proxy)
  * Constrains dnscrypt-proxy with AppArmor and cgroups CPU and memory limitations
* **SSH Tunneling**
  * Adds a restricted `algo` group with no shell access and limited SSH forwarding options
  * Creates one limited, local account per user and an SSH public key for each
