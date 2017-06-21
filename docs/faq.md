# FAQ

* [Has Algo been audited?](#has-algo-been-audited)
* [Why aren't you using Tor?](#why-arent-you-using-tor)
* [Why aren't you using Racoon, LibreSwan, or OpenSwan?](#why-arent-you-using-racoon-libreswan-or-openswan)
* [Why aren't you using a memory-safe or verified IKE daemon?](#why-arent-you-using-a-memory-safe-or-verified-ike-daemon)
* [Why aren't you using OpenVPN?](#why-arent-you-using-openvpn)
* [Why aren't you using Alpine Linux, OpenBSD, or HardenedBSD?](#why-arent-you-using-alpine-linux-openbsd-or-hardenedbsd)
* [I deployed an Algo server. Can you update it with new features?](#i-deployed-an-algo-server-can-you-update-it-with-new-features)
* [Where did the name "Algo" come from?](#where-did-the-name-algo-come-from)

## Has Algo been audited?

No. This project is under active development. We're happy to [accept and fix issues](https://github.com/trailofbits/algo/issues) as they are identified. Use Algo at your own risk. If you find a security issue of any severity, please [contact us on Slack](https://empireslacking.herokuapp.com).

## Why aren't you using Tor?

The goal of this project is not to provide anonymity, but to ensure confidentiality of network traffic. Tor introduces new risks that are unsuitable for Algo's intended users. Namely, with Algo, users are in control over the gateway routing their traffic. With Tor, users are at the mercy of [actively](https://www.securityweek2016.tu-darmstadt.de/fileadmin/user_upload/Group_securityweek2016/pets2016/10_honions-sanatinia.pdf) [malicious](https://web.archive.org/web/20150705184539/https://chloe.re/2015/06/20/a-month-with-badonions/) [exit](https://community.fireeye.com/people/archit.mehta/blog/2014/11/18/onionduke-apt-malware-distributed-via-malicious-tor-exit-node) [nodes](https://www.wired.com/2010/06/wikileaks-documents/).

## Why aren't you using Racoon, LibreSwan, or OpenSwan?

Racoon does not support IKEv2. Racoon2 supports IKEv2 but is not actively maintained. When we looked, the documentation for strongSwan was better than the corresponding documentation for LibreSwan or OpenSwan. strongSwan also has the benefit of a from-scratch rewrite to support IKEv2. I consider such rewrites a positive step when supporting a major new protocol version.

## Why aren't you using a memory-safe or verified IKE daemon?

I would, but I don't know of any [suitable ones](https://github.com/trailofbits/algo/issues/68). If you're in the position to fund the development of such a project, [contact us](mailto:info@trailofbits.com). We would be interested in leading such an effort. At the very least, I plan to make modifications to strongSwan and the environment it's deployed in that prevent or significantly complicate exploitation of any latent issues.

## Why aren't you using OpenVPN?

OpenVPN does not have out-of-the-box client support on any major desktop or mobile operating system. This introduces user experience issues and requires the user to [update](https://www.exploit-db.com/exploits/34037/) and [maintain](https://www.exploit-db.com/exploits/20485/) the software themselves. OpenVPN depends on the security of [TLS](https://tools.ietf.org/html/rfc7457), both the [protocol](https://arstechnica.com/security/2016/08/new-attack-can-pluck-secrets-from-1-of-https-traffic-affects-top-sites/) and its [implementations](https://arstechnica.com/security/2014/04/confirmed-nasty-heartbleed-bug-exposes-openvpn-private-keys-too/), and we simply trust the server less due to [past](https://sweet32.info/) [security](https://github.com/ValdikSS/openvpn-fix-dns-leak-plugin/blob/master/README.md) [incidents](https://www.exploit-db.com/exploits/34879/).

## Why aren't you using Alpine Linux, OpenBSD, or HardenedBSD?

Alpine Linux is not supported out-of-the-box by any major cloud provider. We are interested in supporting Free-, Open-, and HardenedBSD. Follow along or contribute to our BSD support in [this issue](https://github.com/trailofbits/algo/issues/35).

## I deployed an Algo server. Can you update it with new features?

No. By design, the Algo development team has no access to any Algo server that our users haved deployed. We cannot modify the configuration, update the software, or sniff the traffic that goes through your personal Algo VPN server. This prevents scenarios where we are legally compelled or hacked to push down backdoored updates that surveil our users.

As a result, once your Algo server has been deployed, it is yours to maintain. If you want to take advantage of new features available in the current release of Algo, then you have two options. You can use the [SSH administrative interface](/README.md#ssh-into-algo-server) to make the changes you want on your own or you can shut down the server and deploy a new one (recommended).

In the future, we will make it easier for users who want to update their own servers by providing official releases of Algo. Each official release will summarize the changes from the last release to make it easier to follow along with them.

## Where did the name "Algo" come from?

Algo is short for "Al Gore", the **V**ice **P**resident of **N**etworks everywhere for [inventing the Internet](https://www.youtube.com/watch?v=BnFJ8cHAlco).
