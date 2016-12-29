# Algo VPN

[![Slack Status](https://empireslacking.herokuapp.com/badge.svg)](https://empireslacking.herokuapp.com)

Algo VPN (short for "Al Gore", the **V**ice **P**resident of **N**etworks everywhere for [inventing the Internet](https://www.youtube.com/watch?v=BnFJ8cHAlco)) is a set of Ansible scripts that simplifies the setup of a personal IPSEC VPN. It contains the most secure defaults available, works with common cloud providers, and does not require client software on most devices.

## Features

* Supports only IKEv2 w/ a single cipher suite: AES-GCM, HMAC-SHA2, and P-256 DH
* Generates Apple Profiles to auto-configure iOS and macOS devices
* Provides helper scripts to add and remove users
* Blocks ads with a local DNS resolver and HTTP proxy (optional)
* Sets up limited SSH users for tunneling traffic (optional)
* Based on current versions of Ubuntu and strongSwan
* Installs to DigitalOcean, Amazon EC2, Google Cloud Engine, Microsoft Azure or your own server

## Anti-features

* Does not support legacy cipher suites or protocols like L2TP, IKEv1, or RSA
* Does not install Tor, OpenVPN, or other risky servers
* Does not depend on the security of [TLS](https://tools.ietf.org/html/rfc7457)
* Does not require client software on most platforms
* Does not claim to provide anonymity or censorship avoidance
* Does not claim to protect you from the [FSB](https://en.wikipedia.org/wiki/Federal_Security_Service), [MSS](https://en.wikipedia.org/wiki/Ministry_of_State_Security_(China)), [DGSE](https://en.wikipedia.org/wiki/Directorate-General_for_External_Security), or [FSM](https://en.wikipedia.org/wiki/Flying_Spaghetti_Monster)

## Deploy the Algo Server

The easiest way to get an Algo server running is to let it setup a _new_ virtual machine in the cloud for you.

1. Install the dependencies for your operating system:

 OS X: `sudo easy_install pip && sudo pip install --ignore-install -r requirements.txt`
 
 Linux (deb-based): `sudo easy_install pip && sudo apt-get update && sudo apt-get install build-essential libssl-dev libffi-dev python-dev && sudo pip install -r requirements.txt`

 Linux (rpm-based): See the [Pre-Install Documentation for RedHat/CentOS 6.x](docs/pre-install_redhat_centos_6.x.md)

2. Open the file `config.cfg` in your favorite text editor. Specify the users you wish to create in the `users` list.
3. Start the deploy and follow the instructions: `./algo`

That's it! You now have an Algo VPN server on the internet.

Note: for local or scripted deployment instructions see the [Advanced Usage](/docs/ADVANCED.md) documentation.

## Configure the VPN Clients

Certificates and configuration files that users will need are placed in the `configs` directory. Make sure to secure these files since many contain private keys. All files are prefixed with the IP address of the Algo VPN server.

### Apple Devices

Find the corresponding mobileconfig (Apple Profile) for each user and send it to them over AirDrop or other secure means. Apple Configuration Profiles are all-in-one configuration files for iOS and macOS devices. On macOS, double-clicking a profile to install it will fully configure the VPN. On iOS, users are prompted to install the profile as soon as the AirDrop is accepted.

### Android Devices

You need to install the [StrongSwan VPN Client for Android 4 and newer](https://play.google.com/store/apps/details?id=org.strongswan.android). Import the corresponding user.p12 certificate to your device. It's very simple to configure the StrongSwan VPN Client, just make a new profile with the IP address of your VPN server and choose which certificate to use.

### Windows

Copy the CA certificate, user certificate, and the user PowerShell script to the client computer. Import the CA certificate to the local machine Trusted Root certificate store. Then, run the included PowerShell script to import the user certificate, set up a VPN connection, and activate stronger ciphers on it.

If you want to perform these steps by hand, you will need to import the user certificate to the Personal certificate store, add an IKEv2 connection in the network settings, then activate stronger ciphers on it via the following PowerShell script:

`Set-VpnConnectionIPsecConfiguration -ConnectionName "Algo" -AuthenticationTransformConstants SHA25612
8 -CipherTransformConstants AES256 -EncryptionMethod AES256 -IntegrityCheckMethod SHA256 -DHGroup Group14 -PfsGroup none`

### Linux strongSwan Clients (e.g., OpenWRT, Ubuntu, etc.)

Install strongSwan, then copy the included user_ipsec.conf, user_ipsec.secrets, user.crt (user certificate), and user.key (private key) files to your client device. These may require some customization based on your exact use case. These files were originally generated with a point-to-point OpenWRT-based VPN in mind.

### Other Devices

Depending on the platform, you may need one or multiple of the following files.

* ca.crt: CA Certificate
* user_ipsec.conf: StrongSwan client configuration
* user_ipsec.secrets: StrongSwan client configuration
* user.crt: User Certificate
* user.key: User Private Key
* user.mobileconfig: Apple Profile
* user.p12: User Certificate and Private Key (in PKCS#12 format)
* user_windows.ps1: Powershell script to setup a VPN connection on Windows

## Setup an SSH Tunnel

If you turned on the optional SSH tunneling role, then local user accounts will be created for each user in `config.cfg` and an SSH authorized_key files for them will be in the `configs` directory (user.ssh.pem). SSH user accounts do not have shell access and their tunneling options are limited (`ssh -N` is required). This is done to ensure that users have the least access required to tunnel through the server. 

Use the command below to start an SSH tunnel, replacing `ip` and `user` with your own. Once the tunnel is setup, you can configure a browser or other application to use 127.0.0.1:1080 as a SOCKS proxy to route traffic through Algo.

 `ssh -D 127.0.0.1:1080 -f -q -C -N user@ip -i configs/ip_user.ssh.pem`  

## Adding or Removing Users

Algo's own scripts can easily add and remove users from the VPN server.

1. Update the `users` list in your `config.cfg`
2. Run the command: `./algo update-users`

The Algo VPN server now contains only the users listed in the `config.cfg` file.

## FAQ

### Has Algo been audited?

No. This project is under active development. We're happy to [accept and fix issues](https://github.com/trailofbits/algo/issues) as they are identified. Use Algo at your own risk. If you find a security issue of any severity, please [contact us on Slack](https://empireslacking.herokuapp.com).

### Why aren't you using Tor?

The goal of this project is not to provide anonymity, but to ensure confidentiality of network traffic while traveling. Tor introduces new risks that are unsuitable for Algo's intended users. Namely, with Algo, users are in control over the gateway routing their traffic. With Tor, users are at the mercy of [actively](https://www.securityweek2016.tu-darmstadt.de/fileadmin/user_upload/Group_securityweek2016/pets2016/10_honions-sanatinia.pdf) [malicious](https://chloe.re/2015/06/20/a-month-with-badonions/) [exit](https://community.fireeye.com/people/archit.mehta/blog/2014/11/18/onionduke-apt-malware-distributed-via-malicious-tor-exit-node) [nodes](https://www.wired.com/2010/06/wikileaks-documents/).

### Why aren't you using Racoon, LibreSwan, or OpenSwan?

Racoon does not support IKEv2. Racoon2 supports IKEv2 but is not actively maintained. When we looked, the documentation for StrongSwan was better than the corresponding documentation for LibreSwan or OpenSwan. StrongSwan also has the benefit of a from-scratch rewrite to support IKEv2. I consider such rewrites a positive step when supporting a major new protocol version.

### Why aren't you using a memory-safe or verified IKE daemon?

I would, but I don't know of any [suitable ones](https://github.com/trailofbits/algo/issues/68). If you're in the position to fund the development of such a project, [contact us](mailto:info@trailofbits.com). We would be interested in leading such an effort. At the very least, I plan to make modifications to StrongSwan and the environment it's deployed in that prevent or significantly complicate exploitation of any latent issues.

### Why aren't you using OpenVPN?

OpenVPN does not have out-of-the-box client support on any major desktop or mobile operating system. This introduces user experience issues and requires the user to [update](https://www.exploit-db.com/exploits/34037/) and [maintain](https://www.exploit-db.com/exploits/20485/) the software themselves. OpenVPN depends on the security of [TLS](https://tools.ietf.org/html/rfc7457), both the [protocol](http://arstechnica.com/security/2016/08/new-attack-can-pluck-secrets-from-1-of-https-traffic-affects-top-sites/) and its [implementations](http://arstechnica.com/security/2014/04/confirmed-nasty-heartbleed-bug-exposes-openvpn-private-keys-too/), and we simply trust the server less due to [past](https://sweet32.info/) [security](https://github.com/ValdikSS/openvpn-fix-dns-leak-plugin/blob/master/README.md) [incidents](https://www.exploit-db.com/exploits/34879/).

### Why aren't you using Alpine Linux, OpenBSD, or HardenedBSD?

Alpine Linux is not supported out-of-the-box by any major cloud provider. We are interested in supporting Free-, Open-, and HardenedBSD. Follow along or contribute to our BSD support in [this issue](https://github.com/trailofbits/algo/issues/35).
