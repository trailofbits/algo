# Algo

[![Slack Status](https://empireslacking.herokuapp.com/badge.svg)](https://empireslacking.herokuapp.com)

Algo (short for "Al Gore", the **V**ice **P**resident of **N**etworks everywhere for [inventing the Internet](https://www.youtube.com/watch?v=BnFJ8cHAlco)) is a set of Ansible scripts that simplifies the setup of an IPSEC VPN. It contains the most secure defaults available, works with common cloud providers, and does not require client software on most devices.

## Features

* Supports only IKEv2
* Supports only AES GCM, SHA2 HMAC, and P-256 DH
* Generates mobileconfig profiles to auto-configure Apple devices
* Provides helper scripts to add and remove users

## Anti-features

* Does not support legacy cipher suites or protocols, like L2TP or IKEv1
* Does not install Tor, OpenVPN, or other insecure servers
* Does not require client software on most platforms
* Does not claim to provide anonymity or protection from the FSB, MSS, DGSE, or FSM

## Requirements

* ansible >= 2.2.0  
* python >= 2.6  
* dopy  

## Usage

* Open the file `config.cfg` in your favorite text editor. Change `server_name` and specify users in the `users` list.
* Start the deploy and follow the instructions: 
```
ansible-playbook deploy.yml
```
* When the process is done, you can find `.mobileconfig` files and certificates in the `configs` directory. Send the `.mobileconfig` profile to your users on iOS or macOS (note: Profile installation is supported over AirDrop) or send the X.509 certificates to those using other clients, like Windows or Android.
* When the deploy proccess is done a new server will be placed in the local inventory file `inventory_users`.
* If you want to add or delete users, just update the (`users`) list in the config file (`config.cfg`) and run the playbook `users.yml`. This command will update users on all the servers in the file `inventory_users`. If you want to limit servers, you can use option `-l`.
```
ansible-playbook users.yml -i inventory_users
ansible-playbook users.yml -i inventory_users -l vpnserver.com
```

## FAQ

### Has this been audited?

No.

### Why aren't you using Tor?

The goal of this project is not to provide anonymity, but to ensure confidentiality of network traffic while traveling. While Tor may route everything over an encrypted tunnel as well, it introduces new risks that are unsuitable for algo's intended usesrs. Namely, with algo, users are in control over the gateway routing their traffic. With Tor, users are at the mercy of [actively](https://www.securityweek2016.tu-darmstadt.de/fileadmin/user_upload/Group_securityweek2016/pets2016/10_honions-sanatinia.pdf) [malicious](https://chloe.re/2015/06/20/a-month-with-badonions/) [exit](https://community.fireeye.com/people/archit.mehta/blog/2014/11/18/onionduke-apt-malware-distributed-via-malicious-tor-exit-node) [nodes](https://www.wired.com/2010/06/wikileaks-documents/).
