# Algo VPN

[![Slack Status](https://empireslacking.herokuapp.com/badge.svg)](https://empireslacking.herokuapp.com)

Algo VPN (short for "Al Gore", the **V**ice **P**resident of **N**etworks everywhere for [inventing the Internet](https://www.youtube.com/watch?v=BnFJ8cHAlco)) is a set of Ansible scripts that simplifies the setup of a personal IPSEC VPN. It contains the most secure defaults available, works with common cloud providers, and does not require client software on most devices.

## Features

* Supports only IKEv2
* Supports only a single cipher suite w/ AES GCM, SHA2 HMAC, and P-256 DH
* Generates mobileconfig profiles to auto-configure Apple devices
* Provides helper scripts to add and remove users
* Blocks ads with a local DNS resolver and HTTP proxy (optional)
* Based on current versions of Ubuntu and StrongSwan
* Installs to DigitalOcean, Amazon EC2, Google Cloud Engine, or your own server

## Anti-features

* Does not support legacy cipher suites or protocols like L2TP, IKEv1, or RSA
* Does not install Tor, OpenVPN, or other risky servers
* Does not depend on the security of [TLS](https://tools.ietf.org/html/rfc7457)
* Does not require client software on most platforms
* Does not claim to provide anonymity or censorship avoidance
* Does not claim to protect you from the [FSB](https://en.wikipedia.org/wiki/Federal_Security_Service), [MSS](https://en.wikipedia.org/wiki/Ministry_of_State_Security_(China)), [DGSE](https://en.wikipedia.org/wiki/Directorate-General_for_External_Security), or [FSM](https://en.wikipedia.org/wiki/Flying_Spaghetti_Monster)

## Included Roles

Ansible scripts are organized into roles. The roles used by Algo are described in detail below.

### Required Roles

* **Common**
  * Installs several required packages and software updates, then reboots if necessary
  * Configures network interfaces and enables packet forwarding on them
* **VPN**
  * Installs [StrongSwan](https://www.strongswan.org/), enables AppArmor, limits CPU and memory access, and drops user privileges
  * Builds a Certificate Authority (CA) with [easy-rsa-ipsec](https://github.com/ValdikSS/easy-rsa-ipsec) and creates one client certificate per user
  * Bundles the appropriate certificates into Apple mobileconfig profiles for each user

### Optional Roles

* **Security Enhancements**
  * Enables [unattended-upgrades](https://help.ubuntu.com/community/AutomaticSecurityUpdates) to ensure available patches are always applied
  * Modify operating system features like core dumps, kernel parameters, and SUID binaries to limit possible attacks
  * Modifies SSH to use only modern ciphers and a seccomp sandbox, and restricts access to many legacy and unwanted features, like X11 forwarding and SFTP
  * Configures IPtables to block traffic that might pose a risk to VPN users, such as [SMB/CIFS](https://medium.com/@ValdikSS/deanonymizing-windows-users-and-capturing-microsoft-and-vpn-accounts-f7e53fe73834)
* **Ad Blocking and Compression HTTP Proxy**
  * Installs [Privoxy](https://www.privoxy.org/) with an ad blocking ruleset
  * Installs Apache with [mod_pagespeed](http://modpagespeed.com/) as an HTTP proxy
  * Constrains Privoxy and Apache with AppArmor and cgroups CPU and memory limitations
* **DNS Ad Blocking**
  * Install the [dnsmasq](http://www.thekelleys.org.uk/dnsmasq/doc.html) local resolver with a blacklist for advertising domains
  * Constrains dnsmasq with AppArmor and cgroups CPU and memory limitations
* **Security Monitoring and Logging**
  * Configures [auditd](https://access.redhat.com/documentation/en-US/Red_Hat_Enterprise_Linux/6/html/Security_Guide/chap-system_auditing.html) and rsyslog to log data useful for investigating security incidents
  * Emails aggregated Logs to a configured address on a regular basis
* **SSH Tunneling**
  * Adds a restricted `algo` group to SSH with no shell access and limited forwarding options
  * Creates one limited, local account per user and an SSH public key for each

## Usage

### Requirements

* ansible >= 2.1
* python >= 2.6
* [dopy=0.3.5](https://github.com/Wiredcraft/dopy)
* [boto](https://github.com/boto/boto)
* [azure >= 0.7.1](https://github.com/Azure/azure-sdk-for-python)
* [apache-libcloud](https://github.com/apache/libcloud)
* [libcloud](https://curl.haxx.se/docs/caextract.html) (for Mac OS)
* [six](https://github.com/JioCloud/python-six) 
* SHell or BASH
* libselinux-python (for RedHat based distros)

### Roles and Tags
**Cloud roles:**  
- role: cloud-digitalocean, tags: digitalocean
- role: cloud-ec2, tags: ec2  
- role: cloud-gce, tags: gce  

**Server roles:**  
- role: vpn, tags: vpn 
- role: dns_adblocking, tags: dns, adblock
- role: proxy, tags: proxy, adblock 
- role: logging, tags: logging
- role: security, tags: security
- role: ssh_tunneling, tags: ssh_tunneling

### Cloud Providers

**digitalocean**  
*Requirement variables:*  
- do_access_token  
- do_ssh_name  
- do_server_name  
- do_region

*Possible regions:*  
- ams2
- ams3
- fra1
- lon1
- nyc1
- nyc2
- nyc3
- sfo1
- sfo2
- sgp1
- tor1
- blr1

**gce**  
*Requirement variables:*  
- credentials_file
- server_name
- ssh_public_key
- zone

*Possible zones:*  
- us-central1-a
- us-central1-b
- us-central1-c
- us-central1-f
- us-east1-b
- us-east1-c
- us-east1-d
- europe-west1-b
- europe-west1-c
- europe-west1-d
- asia-east1-a
- asia-east1-b
- asia-east1-c

**ec2**  
*Requirement variables:*  
- aws_access_key
- aws_secret_key
- aws_server_name
- ssh_public_key
- region

*Possible regions:*  
- us-east-1
- us-west-1
- us-west-2
- ap-south-1
- ap-northeast-2
- ap-southeast-1
- ap-southeast-2
- ap-northeast-1
- eu-central-1
- eu-west-1
- sa-east-1

### Cloud Deployment

To install the dependencies on OS X or Linux:

```
sudo easy_install pip
sudo pip install -r requirements.txt
```

Open the file `config.cfg` in your favorite text editor. Specify the users you wish to create in the `users` list.

Start the deploy with extra variables and tags that you need.  
Example for DigitalOcean:

```
ansible-playbook deploy.yml -t digitalocean,vpn -e 'do_access_token=secret_token do_ssh_name=my_ssh_key do_server_name=algo.local do_region=ams2'
```

When the process is done, you can find `.mobileconfig` files and certificates in the `configs` directory. Send the `.mobileconfig` profile to users with Apple devices. Note that profile installation is supported over AirDrop. Do not send the mobileconfig file over plaintext (e.g., e-mail) since it contains the keys to access the VPN. For those using other clients, like Windows or Android, securely send them the X.509 certificates for the server and their user.  

### Local Deployment

It is possible to download Algo to your own Ubuntu server and run the scripts locally. You need to install ansible to run Algo on Ubuntu. Installing ansible via pip requires pulling in a lot of dependencies, including a full compiler suite. It is easier to use apt, however, Ubuntu 16.04 only comes with ansible 2.0.0.2. Therefore, to use apt you must use the ansible PPA and using a PPA requires installing `software-properties-common`. tl;dr:
```
sudo apt-get install software-properties-common && sudo apt-add-repository ppa:ansible/ansible
sudo apt-get update && sudo apt-get install ansible
git clone https://github.com/trailofbits/algo
cd algo && ./algo
```

### User Management

If you want to add or delete users, update the `users` list in `config.cfg` and run the command: 

```
./algo update-users
```

## FAQ

### Has this been audited?

No. This project is under active development. We're happy to [accept and fix issues](https://github.com/trailofbits/algo/issues) as they are identified. Use algo at your own risk.

### Why aren't you using Tor?

The goal of this project is not to provide anonymity, but to ensure confidentiality of network traffic while traveling. Tor introduces new risks that are unsuitable for Algo's intended users. Namely, with algo, users are in control over the gateway routing their traffic. With Tor, users are at the mercy of [actively](https://www.securityweek2016.tu-darmstadt.de/fileadmin/user_upload/Group_securityweek2016/pets2016/10_honions-sanatinia.pdf) [malicious](https://chloe.re/2015/06/20/a-month-with-badonions/) [exit](https://community.fireeye.com/people/archit.mehta/blog/2014/11/18/onionduke-apt-malware-distributed-via-malicious-tor-exit-node) [nodes](https://www.wired.com/2010/06/wikileaks-documents/).

### Why aren't you using Racoon, LibreSwan, or OpenSwan?

Raccoon does not support IKEv2. Racoon2 supports IKEv2 but is not actively maintained. When we looked, the documentation for StrongSwan was better than the corresponding documentation for LibreSwan or OpenSwan. StrongSwan also has the benefit of a from-scratch rewrite to support IKEv2. I consider such rewrites a positive step when supporting a major new protocol version.

### Why aren't you using a memory-safe or verified IKE daemon?

I would, but I don't know of any [suitable ones](https://github.com/trailofbits/algo/issues/68). If you're in the position to fund the development of such a project, [contact us](mailto:info@trailofbits.com). We would be interested in leading such an effort. At the very least, I plan to make modifications to StrongSwan and the environment it's deployed in that prevent or significantly complicate exploitation of any latent issues.

### Why aren't you using OpenVPN?

OpenVPN does not have out-of-the-box client support on any major desktop or mobile operating system. This introduces user experience issues and requires the user to [update](https://www.exploit-db.com/exploits/34037/) and [maintain](https://www.exploit-db.com/exploits/20485/) the software themselves. OpenVPN depends on the security of [TLS](https://tools.ietf.org/html/rfc7457), both the [protocol](http://arstechnica.com/security/2016/08/new-attack-can-pluck-secrets-from-1-of-https-traffic-affects-top-sites/) and its [implementations](http://arstechnica.com/security/2014/04/confirmed-nasty-heartbleed-bug-exposes-openvpn-private-keys-too/), and we simply trust the server less due to past [security](https://github.com/ValdikSS/openvpn-fix-dns-leak-plugin/blob/master/README.md) [incidents](https://www.exploit-db.com/exploits/34879/).

### Why aren't you using Alpine Linux, OpenBSD, or HardenedBSD?

Alpine Linux is not supported out-of-the-box by any major cloud provider. We are interested in supporting Free, Open, and HardenedBSD. Follow along on our progress in [this issue](https://github.com/trailofbits/algo/issues/35).
