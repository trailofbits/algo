# AlgoVPN and Firewalls

Your AlgoVPN requires properly configured firewalls. The key points to know are:

* If you deploy to a **cloud** provider all firewall configuration will done automatically.

* If you perform a **local** installation on an existing server you are responsible for configuring any external firewalls. You must also take care not to interfere with the server firewall configuration of the AlgoVPN.

## The Two Types of Firewall

![Firewall Illustration](/docs/images/firewalls.png)

### Server Firewall

During installation Algo configures the Linux [Netfilter](https://en.wikipedia.org/wiki/Netfilter) firewall on the server. The rules added are required for AlgoVPN to work properly. The package `netfilter-persistent` is used to load the IPv4 and IPv6 rules files that Algo generates and stores in `/etc/iptables`. The rules for IPv6 are only generated if the server appears to be properly configured for IPv6. The use of conflicting firewall packages on the server such as `ufw` will likely break AlgoVPN.

### External Firewall

Most cloud service providers offer a firewall that sits between the Internet and your AlgoVPN. With some providers (such as EC2, Lightsail, and GCE) this firewall is required and is configured by Algo during a **cloud** deployment. If the firewall is not required by the provider then Algo does not configure it.

External firewalls are not configured when performing a **local** installation, even when using a server from a cloud service provider.

Any external firewall must be configured to pass the following incoming ports over IPv4 :

Port | Protocol | Description | Related variables in `config.cfg`
---- | -------- | ----------- | ---------------------------------
4160  | TCP | Secure Shell (SSH) | `ssh_port` (**cloud** only; for **local** port remains 22)
500   | UDP | IPsec IKEv2 | `ipsec_enabled`
4500  | UDP | IPsec NAT-T | `ipsec_enabled`
51820 | UDP | WireGuard | `wireguard_enabled`, `wireguard_port`

If you have chosen to disable either IPsec or WireGuard in `config.cfg` before running `./algo` then the corresponding ports don't need to pass through the firewall. SSH is used when performing a **cloud** deployment and when subsequently modifying the list of VPN users by running `./algo update-users`.

Even when not required by the cloud service provider, you still might wish to use an external firewall to limit SSH access to your AlgoVPN to connections from certain IP addresses, or perhaps to block SSH access altogether if you don't need it. Every service provider firewall is different so refer to the provider's documentation for more information.
