#!/usr/bin/env bash

set -ex

USER_ARGS="{ 'server': '10.0.8.100', 'users': ['desktop', 'user1', 'user2'], 'local_service_ip': '172.16.0.1', 'no_log': false }"

if [ "${DEPLOY}" == "docker" ]
then
  docker run -i -v $(pwd)/config.cfg:/algo/config.cfg -v ~/.ssh:/root/.ssh -v $(pwd)/configs:/algo/configs -e "USER_ARGS=${USER_ARGS}" local/algo /bin/sh -c "chown -R root: /root/.ssh && chmod -R 600 /root/.ssh && source .env/bin/activate && ansible-playbook users.yml -e \"${USER_ARGS}\" -t update-users --skip-tags debug -vvvvv"
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

if sudo openssl x509 -inform pem -noout -text -in configs/10.0.8.100/ipsec/.pki/certs/user1.crt | grep -E "CN(=|\s+=\s+)user1"
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
