# FAQ

* [Has Algo been audited?](#has-algo-been-audited)
* [What's the current status of WireGuard?](#whats-the-current-status-of-wireguard)
* [Why aren't you using Tor?](#why-arent-you-using-tor)
* [Why aren't you using Racoon, LibreSwan, or OpenSwan?](#why-arent-you-using-racoon-libreswan-or-openswan)
* [Why aren't you using a memory-safe or verified IKE daemon?](#why-arent-you-using-a-memory-safe-or-verified-ike-daemon)
* [Why aren't you using OpenVPN?](#why-arent-you-using-openvpn)
* [Why aren't you using Alpine Linux, OpenBSD, or HardenedBSD?](#why-arent-you-using-alpine-linux-openbsd-or-hardenedbsd)
* [I deployed an Algo server. Can you update it with new features?](#i-deployed-an-algo-server-can-you-update-it-with-new-features)
* [Where did the name "Algo" come from?](#where-did-the-name-algo-come-from)
* [Can DNS filtering be disabled?](#can-dns-filtering-be-disabled)
* [Wasn't IPSEC backdoored by the US government?](#wasnt-ipsec-backdoored-by-the-us-government)
* [What inbound ports are used?](#what-inbound-ports-are-used)
* [How do I monitor user activity?](#how-do-i-monitor-user-activity)
* [How do I reach another connected client?](#how-do-i-reach-another-connected-client)

## Has Algo been audited?

No. This project is under active development. We're happy to [accept and fix issues](https://github.com/trailofbits/algo/issues) as they are identified. Use Algo at your own risk. If you find a security issue of any severity, please [contact us on Slack](https://slack.empirehacking.nyc).

## What's the current status of WireGuard?

[WireGuard reached "stable" 1.0.0 release](https://lists.zx2c4.com/pipermail/wireguard/2020-March/005206.html) in Spring 2020. It has undergone [substantial](https://www.wireguard.com/formal-verification/) security review.

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

No. By design, the Algo development team has no access to any Algo server that our users have deployed. We cannot modify the configuration, update the software, or sniff the traffic that goes through your personal Algo VPN server. This prevents scenarios where we are legally compelled or hacked to push down backdoored updates that surveil our users.

As a result, once your Algo server has been deployed, it is yours to maintain. It will use unattended-upgrades by default to apply security and feature updates to Ubuntu, as well as to the core VPN software of strongSwan, dnscrypt-proxy and WireGuard. However, if you want to take advantage of new features available in the current release of Algo, then you have two options. You can use the [SSH administrative interface](/README.md#ssh-into-algo-server) to make the changes you want on your own or you can shut down the server and deploy a new one (recommended).

As an extension of this rationale, most configuration options (other than users) available in `config.cfg` can only be set at the time of initial deployment.

## Where did the name "Algo" come from?

Algo is short for "Al Gore", the **V**ice **P**resident of **N**etworks everywhere for [inventing the Internet](https://www.youtube.com/watch?v=BnFJ8cHAlco).

## Can DNS filtering be disabled?

You can temporarily disable DNS filtering for all IPsec clients at once with the following workaround: SSH to your Algo server (using the 'shell access' command printed upon a successful deployment), edit `/etc/ipsec.conf`, and change `rightdns=<random_ip>` to `rightdns=8.8.8.8`. Then run `sudo systemctl restart strongswan`. DNS filtering for WireGuard clients has to be disabled on each client device separately by modifying the settings in the app, or by directly modifying the `DNS` setting on the `clientname.conf` file. If all else fails, we recommend deploying a new Algo server without the adblocking feature enabled.

## Wasn't IPSEC backdoored by the US government?

No.

[Per security researcher Thomas Ptacek](https://news.ycombinator.com/item?id=2014197):

> In 2001, Angelos Keromytis --- then a grad student at Penn, now a Columbia professor --- added support for hardware-accelerated IPSEC NICs. When you have an IPSEC NIC, the channel between the NIC and the IPSEC stack keeps state to tell the stack not to bother doing the things the NIC already did, among them validating the IPSEC ESP authenticator. Angelos' code had a bug; it appears to have done the software check only when the hardware had already done it, and skipped it otherwise.
>
> The bug happened during a change that simultaneously refactored and added a feature to OpenBSD's ESP code; a comparison that should have been == was instead !=; the "if" statement with the bug was originally and correctly !=, but should have been flipped based on how the code was refactored.
>
> HD Moore may as we speak be going through the pain of reconstituting a nearly decade-old version of OpenBSD to verify the bug, but stipulate that it was there, and here's what you get: IPSEC ESP packet authentication was disabled if you didn't have hardware IPSEC. There is probably an elaborate man-in-the-middle scenario in which this could get you traffic inspection, but it's nowhere nearly as straightforward as leaking key bits.
>
> To entertain the conspiracy theory, you're still suggesting that the FBI not only introduced this bug, but also developed the technology required to MITM ESP sessions, bouncing them through some secret FBI-developed middlebox.
>
> One year later, Jason Wright from NETSEC (the company at the heart of the [I think silly] allegations about OpenBSD IPSEC backdoors) fixed the bug.
>
> It's interesting that the bug was fixed without an advisory (oh to be a fly on the wall on ICB that day; Theo had a, um, a, "way" with his dev team). On the other hand, we don't know what releases of OpenBSD actually had the bug right now.
>
> It seems vanishingly unlikely that there could have been anything deliberate about this series of changes. You are unlikely to find anyone who will impugn Angelos. Meanwhile, the diffs tell exactly the opposite of the story that Greg Perry told.

## What inbound ports are used?

You should only need 4160/TCP, 500/UDP, 4500/UDP, and 51820/UDP opened on any firewall that sits between your clients and your Algo server. See [AlgoVPN and Firewalls](/docs/firewalls.md) for more information.

## How do I monitor user activity?

Your Algo server will track IPsec client logins by default in `/var/log/syslog`. This will give you client names, date/time of connection and reconnection, and what IP addresses they're connecting from. This can be disabled entirely by setting `strongswan_log_level` to `-1` in `config.cfg`. WireGuard doesn't save any logs, but entering `sudo wg` on the server will give you the last endpoint and contact time of each client. Disabling this is [paradoxically difficult](https://git.zx2c4.com/blind-operator-mode/about/). There isn't any out-of-the-box way to monitor actual user _activity_ (e.g. websites browsed, etc.)

## How do I reach another connected client?

By default, your Algo server doesn't allow connections between connected clients. This can be changed at the time of deployment by enabling the `BetweenClients_DROP` flag in `config.cfg`. See the ["Road Warrior" instructions](/docs/deploy-to-ubuntu.md#road-warrior-setup) for more details.
