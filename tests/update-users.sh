#!/usr/bin/env bash

set -ex

USER_ARGS="{ 'server': '10.0.8.100', 'users': ['desktop', 'user1', 'user2'] }"

if [ "${DEPLOY}" == "docker" ]
then
  make docker-ci-user-update
else
  ansible-playbook users.yml -e "${USER_ARGS}" -t update-users
fi

#
# IPsec
#

if sudo openssl crl -inform pem -noout -text -in configs/10.0.8.100/ipsec/.pki/crl/phone.crt | grep CRL
  then
    echo "The CRL check passed"
  else
    echo "The CRL check failed"
    exit 1
fi

if sudo openssl x509 -inform pem -noout -text -in configs/10.0.8.100/ipsec/.pki/certs/user1.crt | grep CN=user1
  then
    echo "The new user exists"
  else
    echo "The new user does not exist"
    exit 1
fi

#
# WireGuard
#

if sudo test -f configs/10.0.8.100/wireguard/user1.conf
  then
    echo "WireGuard: The new user exists"
  else
    echo "WireGuard: The new user does not exist"
    exit 1
fi

#
# SSH tunneling
#

if sudo test -f configs/10.0.8.100/ssh-tunnel/user1.ssh_config
  then
    echo "SSH Tunneling: The new user exists"
  else
    echo "SSH Tunneling: The new user does not exist"
    exit 1
fi
