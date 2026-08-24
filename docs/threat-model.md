# Algo threat model

This document defines what Algo is designed to protect, what it trusts, and the boundary of its **secure core**. It is a maintenance policy as well as user guidance: a feature being technically possible does not make it appropriate for Algo.

## Protected assets and security goals

Algo protects:

* VPN client private keys, IPsec certificates, preshared material, CA keys and the passwords emitted during deployment.
* The cloud credentials and administrative SSH keys used by the deployment controller.
* The integrity of generated client profiles, VPN daemon configuration, firewall rules, routing, DNS configuration, and update policy.
* The confidentiality and integrity of traffic between an uncompromised client and the Algo server, against local-network observers, an ISP on the access path, and opportunistic Internet attackers.
* Isolation between VPN clients when `BetweenClients_DROP` is enabled, and exposure of only the network services selected during deployment.

The intended deployment is a personal VPN run by an identifiable administrator for a small set of devices. Credentials must be unique per device. Generated files under `configs/` are secrets and must be stored and transferred accordingly.

## Adversaries in scope

The secure core is intended to resist:

* passive and active attackers on an untrusted access network;
* Internet scanners and unauthenticated attempts against the public server;
* one VPN client attempting to reach another when client isolation is enabled; and
* accidental weakening caused by an insecure default or an unreviewed dependency update.

These goals assume current software, uncompromised endpoints, and uncompromised administrator credentials.

## Trust boundaries and assumptions

An Algo deployment crosses several trust boundaries:

1. **Controller to source and package services.** The administrator trusts the checked-out Algo revision and the dependencies described under [Supply-chain trust](#supply-chain-trust).
2. **Controller to cloud API.** Cloud credentials enter provider SDKs and cloud APIs. The provider account, API, image service, hypervisor, network, and control plane are trusted to create the requested host faithfully.
3. **Controller to server.** Ansible configures the server over SSH. Algo assumes the initial host key or cloud-created instance is authentic and that the controller and server are not already compromised.
4. **Controller to client.** Files and QR codes in `configs/` contain credentials. Their confidentiality depends on the controller filesystem and the channel used to place them on the client.
5. **Client to VPN server.** WireGuard or IKEv2 authenticates and encrypts this path. The client software, operating system, and local key store remain trusted.
6. **VPN server to the Internet.** Traffic is no longer protected by the VPN after it exits the server. Application-layer protection such as HTTPS is still required.

The administrator also trusts the cloud provider not to retain more metadata than its policy states. Algo minimizes its own logs, but cannot prevent provider, destination, DNS, or traffic-correlation observation.

## Supply-chain trust

A deployment relies on more than this repository. Trusted inputs include:

* the Algo Git revision and bootstrap scripts run by the administrator;
* Python distributions from PyPI and the resolved versions in `uv.lock`;
* Ansible collections pinned in `requirements.yml`;
* Ubuntu 22.04 LTS images, archives, security updates, and package signing infrastructure;
* WireGuard, strongSwan, OpenSSH, iptables, and other installed operating-system packages;
* cloud-provider SDKs, APIs, images, metadata services, and hypervisors; and
* optional DNSCrypt resolver metadata and ad-block lists fetched at runtime.

Pins and the `uv` package-age delay reduce accidental drift and exposure to a just-published malicious release; they do not prove that a dependency is benign. Dependency and collection changes must retain lock or exact-version review, automated policy checks, and security scanning. Users requiring stronger provenance should mirror and verify these inputs and build or select their own trusted base image.

## Supported secure core

The secure core is deliberately small:

* the current Algo 2.x line;
* deployment from a trusted controller using Python 3.12 or newer;
* configuration of a fresh Ubuntu 22.04 LTS server with automatic security updates;
* WireGuard and strongSwan IKEv2 using Algo's shipped cryptographic defaults;
* key and client-profile generation, host firewalling, forwarding, and client isolation; and
* key-only administrative SSH used by the deployment workflow.

Cloud provisioning adapters are convenience code outside the VPN protocol boundary. They are included in the secure core only while their create, configure, and destroy paths are maintained and verified against the provider API. **Microsoft Azure is currently excluded and unverified. Amazon Lightsail is currently excluded and unverified.** Their presence in deployment prompts is not a security-support claim. Treat any provider path without current automated and maintainer verification the same way; deploying to an existing, trusted Ubuntu server keeps provider provisioning outside Algo.

Optional DNS encryption, ad blocking, privacy cleanup, and restricted SSH tunneling enlarge the deployment and trust their respective upstream inputs. They are supported configuration options, not prerequisites for a secure VPN.

See [SECURITY.md](../SECURITY.md#supported-versions) for the release support window.

## Non-goals

Algo does **not** promise:

* anonymity, resistance to global traffic analysis, or concealment that a VPN is in use;
* censorship circumvention, traffic obfuscation, domain fronting, or protocol mimicry;
* protection after a client, controller, VPN server, cloud account, provider control plane, or administrator credential is compromised;
* protection of plaintext traffic after it leaves the VPN server;
* a multi-tenant commercial VPN service, identity platform, or general-purpose remote-access gateway;
* a browser-based or public administrative control plane; or
* indefinite in-place upgrades of old deployments. Reprovisioning a fresh host is the preferred security boundary.

## Feature acceptance gate

A proposed feature must pass every gate below before entering the secure core:

1. **Mission fit:** it directly improves a small personal WireGuard/IKEv2 VPN, its safe deployment, or its maintenance.
2. **Threat-model benefit:** it names the protected asset and attacker, and does not make a non-goal appear supported.
3. **Attack-surface discipline:** it avoids new public listeners, long-running privileged services, interpreters, dashboards, and credential stores. Any unavoidable surface must be disabled by default and justified.
4. **Secure default and containment:** least privilege, client isolation, firewall policy, secret handling, update behavior, and failure mode remain at least as strong as before.
5. **Supply-chain budget:** new dependencies are minimal, actively maintained, version-controlled, reviewable, and covered by dependency policy.
6. **Verification:** tests exercise enable, disable, upgrade or reprovision, and failure paths; user and security documentation identify added trust and operational responsibilities.
7. **Maintenance:** a maintainer accepts the ongoing review and compatibility cost. Features may be rejected when that cost dilutes work on the secure core.

An optional flag is not by itself sufficient. Features failing the gate should live in a separate project or downstream integration rather than behind an Algo option.

## Rejected feature requests

The following decisions are examples of the gate in action and are intentional project boundaries:

* [#14959, add Xray support](https://github.com/trailofbits/algo/issues/14959), was rejected. Xray is aimed at proxying, obfuscation, and censorship circumvention; it introduces another network daemon, protocol suite, configuration surface, and supply chain outside Algo's personal VPN mission.
* [#14916, add a web UI](https://github.com/trailofbits/algo/issues/14916), was rejected. A web control plane adds a public application, authentication and session handling, secret management, and a long-lived privileged service for convenience rather than improving tunnel security.

Reconsidering either class of feature requires an explicit threat-model revision, not only an implementation pull request.

## Reporting model gaps

Report exploitable implementation failures privately as described in [SECURITY.md](../SECURITY.md). Public design discussions may propose corrections to assumptions, assets, or boundaries, but should not include vulnerability details or live credentials.
