## FAQ

1. [Has Algo been audited?](#1-has-algo-been-audited)
2. [Why aren't you using Tor?](#2-why-arent-you-using-tor)
3. [Why aren't you using Racoon, LibreSwan, or OpenSwan?](#3-why-arent-you-using-racoon-libreswan-or-openswan)
4. [Why aren't you using a memory-safe or verified IKE daemon?](#4-why-arent-you-using-a-memory-safe-or-verified-ike-daemon)
5. [Why aren't you using OpenVPN?](#5-why-arent-you-using-openvpn)
6. [Why aren't you using Alpine Linux, OpenBSD, or HardenedBSD?](#6-why-arent-you-using-alpine-linux-openbsd-or-hardenedbsd)
7. [Where did the name "Algo" come from?](#7-where-did-the-name-algo-come-from)

### 1. Has Algo been audited?

No. This project is under [active development](https://github.com/trailofbits/algo/projects/1). We're happy to [accept and fix issues](https://github.com/trailofbits/algo/issues) as they are identified. Use Algo at your own risk. If you find a security issue of any severity, please [contact us on Slack](https://empireslacking.herokuapp.com).

### 2. Why aren't you using Tor?

The goal of this project is not to provide anonymity, but to ensure confidentiality of network traffic while traveling. Tor introduces new risks that are unsuitable for Algo's intended users. Namely, with Algo, users are in control over the gateway routing their traffic. With Tor, users are at the mercy of [actively](https://www.securityweek2016.tu-darmstadt.de/fileadmin/user_upload/Group_securityweek2016/pets2016/10_honions-sanatinia.pdf) [malicious](https://chloe.re/2015/06/20/a-month-with-badonions/) [exit](https://community.fireeye.com/people/archit.mehta/blog/2014/11/18/onionduke-apt-malware-distributed-via-malicious-tor-exit-node) [nodes](https://www.wired.com/2010/06/wikileaks-documents/).

### 3. Why aren't you using Racoon, LibreSwan, or OpenSwan?

Racoon does not support IKEv2. Racoon2 supports IKEv2 but is not actively maintained. When we looked, the documentation for strongSwan was better than the corresponding documentation for LibreSwan or OpenSwan. strongSwan also has the benefit of a from-scratch rewrite to support IKEv2. I consider such rewrites a positive step when supporting a major new protocol version.

### 4. Why aren't you using a memory-safe or verified IKE daemon?

I would, but I don't know of any [suitable ones](https://github.com/trailofbits/algo/issues/68). If you're in the position to fund the development of such a project, [contact us](mailto:info@trailofbits.com). We would be interested in leading such an effort. At the very least, I plan to make modifications to strongSwan and the environment it's deployed in that prevent or significantly complicate exploitation of any latent issues.

### 5. Why aren't you using OpenVPN?

OpenVPN does not have out-of-the-box client support on any major desktop or mobile operating system. This introduces user experience issues and requires the user to [update](https://www.exploit-db.com/exploits/34037/) and [maintain](https://www.exploit-db.com/exploits/20485/) the software themselves. OpenVPN depends on the security of [TLS](https://tools.ietf.org/html/rfc7457), both the [protocol](http://arstechnica.com/security/2016/08/new-attack-can-pluck-secrets-from-1-of-https-traffic-affects-top-sites/) and its [implementations](http://arstechnica.com/security/2014/04/confirmed-nasty-heartbleed-bug-exposes-openvpn-private-keys-too/), and we simply trust the server less due to [past](https://sweet32.info/) [security](https://github.com/ValdikSS/openvpn-fix-dns-leak-plugin/blob/master/README.md) [incidents](https://www.exploit-db.com/exploits/34879/).

### 6. Why aren't you using Alpine Linux, OpenBSD, or HardenedBSD?

Alpine Linux is not supported out-of-the-box by any major cloud provider. We are interested in supporting Free-, Open-, and HardenedBSD. Follow along or contribute to our BSD support in [this issue](https://github.com/trailofbits/algo/issues/35).

### 7. Where did the name "Algo" come from?

Algo is short for "Al Gore", the **V**ice **P**resident of **N**etworks everywhere for [inventing the Internet](https://www.youtube.com/watch?v=BnFJ8cHAlco).
