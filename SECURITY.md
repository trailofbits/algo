# Security policy

The Algo team and community take security bugs in Algo seriously. We appreciate responsible disclosure and make every effort to acknowledge useful reports.

Before deploying Algo, read the [threat model and secure-core scope](docs/threat-model.md). It describes the assets Algo protects, required trust assumptions, explicitly unsupported goals, and the feature acceptance policy.

## Supported Versions

Security fixes target the default branch and the most recent release in the 2.x line. Older deployments should be replaced with a fresh server built from a supported revision rather than upgraded indefinitely.

| Version | Security support |
|:--|:--|
| Default branch / latest 2.x release | Yes |
| 2.x pre-release | Best effort; update to the latest revision before reporting |
| 1.x and earlier | No — unsupported |

The version window does not broaden the secure-core platform boundary. In particular, use the controller, server OS, protocol, and provider paths identified in the [supported secure core](docs/threat-model.md#supported-secure-core). A provider offered by a deployment prompt may still be explicitly unverified.

## Reporting Security Issues

Use the GitHub Security Advisory [**Report a vulnerability**](https://github.com/trailofbits/algo/security/advisories/new) form. Do not open a public issue for a suspected vulnerability and do not include live cloud credentials, generated client profiles, private keys, passwords, or identifying deployment logs.

Please include, when available:

* the Algo revision or release and whether local changes were present;
* controller and server versions, deployment provider, and enabled options;
* a description of impact and the affected protected asset;
* minimal reproduction steps or a proof of concept with secrets removed; and
* any mitigations already tested.

The security team will respond with next steps, keep the reporter informed as work progresses, and may ask for more information. Report vulnerabilities in an upstream package or third-party module directly to its maintainer as well; if the issue makes Algo's supported configuration unsafe, also report the impact to Algo privately.
