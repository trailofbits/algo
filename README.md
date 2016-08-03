# Algo

[![Slack Status](https://empireslacking.herokuapp.com/badge.svg)](https://empireslacking.herokuapp.com)

Algo (short for "Al Gore", the **V**ice **P**resident of **N**etworks everywhere for [inventing the Internet](https://www.youtube.com/watch?v=BnFJ8cHAlco)) is a set of Ansible scripts that simplifies the setup of an IPSEC VPN. It contains the most secure defaults available, works with common cloud providers, and does not require client software on most devices.

## Features

* Supports only IKEv2
* Supports only AES GCM, SHA2 HMAC, and P-256 DH
* Generates mobileconfig profiles to auto-configure Apple devices
* Provides helper scripts to add and remove users
* Blocks ads with a local DNS resolver and HTTP proxy (optional)
* Based on current versions of Ubuntu and StrongSwan

## Anti-features

* Does not support legacy cipher suites or protocols like L2TP, IKEv1, or RSA
* Does not install Tor, OpenVPN, or other risky servers
* Does not depend on the security of [TLS](https://tools.ietf.org/html/rfc7457)
* Does not require client software on most platforms
* Does not claim to provide anonymity or censorship avoidance
* Does not claim to protect you from the [FSB](https://en.wikipedia.org/wiki/Federal_Security_Service), [MSS](https://en.wikipedia.org/wiki/Ministry_of_State_Security_(China)), [DGSE](https://en.wikipedia.org/wiki/Directorate-General_for_External_Security), or [FSM](https://en.wikipedia.org/wiki/Flying_Spaghetti_Monster)

## Usage

### Requirements

* ansible >= 2.2.0
* python >= 2.6
* libselinux-python (for RedHat based distros)
* [dopy=0.3.5](https://github.com/Wiredcraft/dopy)

### Initial Deployment

Open the file `config.cfg` in your favorite text editor. Change `server_name` and specify users in the `users` list. Start the deploy and follow the instructions (available options for PROVIDER are `digitalocean` or `ec2`): 

```
ansible-playbook deploy.yml -e "provider=PROVIDER"
```

When the process is done, you can find `.mobileconfig` files and certificates in the `configs` directory. Send the `.mobileconfig` profile to users with Apple devices. Note that profile installation is supported over AirDrop. Do not send the mobileconfig file over plaintext since it contains the keys to access the VPN. For those using other clients, like Windows or Android, send the X.509 certificates for the server and their user.

Note: For EC2 users, ensure that you setup the required environment variables prior to starting the deploy:

```
declare -x AWS_ACCESS_KEY_ID="XXXXXXXXXXXXXXXXXXX"
declare -x AWS_SECRET_ACCESS_KEY="XXXXXXXXXXXXXXXxx"
```

### User Management

When the deploy proccess is done a new server will be placed in the local inventory file `inventory_users`. If you want to add or delete users, update the `users` list in `config.cfg` and run the playbook `users.yml`. This command will update users on any servers in the file `inventory_users`. If you want to limit the servers it updates, you can use `-l` flag.

```
ansible-playbook users.yml -i inventory_users
ansible-playbook users.yml -i inventory_users -l example.com
```

Note: For EC2 users, Algo does NOT use EC2 dynamic inventory for user management. Please continue to use users.yml playbook as described above. This may be subject to change in the future.

## FAQ

### Has this been audited?

No. This project is under active development. We're happy to [accept and fix issues](https://github.com/trailofbits/algo/issues) as they are identified. Use algo at your own risk.

### Why aren't you using Tor?

The goal of this project is not to provide anonymity, but to ensure confidentiality of network traffic while traveling. Tor introduces new risks that are unsuitable for algo's intended users. Namely, with algo, users are in control over the gateway routing their traffic. With Tor, users are at the mercy of [actively](https://www.securityweek2016.tu-darmstadt.de/fileadmin/user_upload/Group_securityweek2016/pets2016/10_honions-sanatinia.pdf) [malicious](https://chloe.re/2015/06/20/a-month-with-badonions/) [exit](https://community.fireeye.com/people/archit.mehta/blog/2014/11/18/onionduke-apt-malware-distributed-via-malicious-tor-exit-node) [nodes](https://www.wired.com/2010/06/wikileaks-documents/).

### Why aren't you using Racoon, LibreSwan, or OpenSwan?

Raccoon does not support IKEv2. Racoon2 supports IKEv2 but is not actively maintained. When we looked, the documentation for StrongSwan was better than the corresponding documentation for LibreSwan or OpenSwan. StrongSwan also has the benefit of a from-scratch rewrite to support IKEv2. We consider such rewrites a positive step when supporting a major new protocol version.

### Why aren't you using a memory-safe or verified IKE daemon?

I would, but I don't know of any. If you're in the position to fund the development of such a project, [contact us](mailto:info@trailofbits.com). We would be interested in leading such an effort. At the very least, we plan to make modifications to StrongSwan and the environment it's deployed in that prevent or significantly complicate exploitation of any latent issues.

### Why aren't you using OpenVPN?

OpenVPN does not have out-of-the-box client support on any major desktop or mobile operating system. This introduces user experience issues and requires the user to update and maintain the software themselves. OpenVPN depends on the security of the [TLS](https://tools.ietf.org/html/rfc7457), both the protocol and its implementations, and we simply trust the server less due to [past security incidents](https://www.exploit-db.com/exploits/34879/).

### Why aren't you using Alpine Linux?

I would, but Alpine Linux is not supported out-of-the-box by any major cloud provider.