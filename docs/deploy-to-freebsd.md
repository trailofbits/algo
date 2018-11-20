# FreeBSD / HardenedBSD server setup

FreeBSD server support is a work in progress. For now, it is only possible to install Algo on existing FreeBSD 11 systems.

## System preparation

Ensure that the following kernel options are enabled:

```
# sysctl kern.conftxt | grep -iE "IPSEC|crypto"
options	IPSEC
options IPSEC_NAT_T
device	crypto
```

## Available roles

* vpn
* ssh_tunneling
* dns_adblocking

## Additional variables

* rebuild_kernel - set to `true` if you want to let Algo to rebuild your kernel if needed (takes a lot of time)

## Installation

```shell
ansible-playbook main.yml -e "provider=local"
```

And follow the instructions
