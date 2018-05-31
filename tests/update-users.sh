#!/usr/bin/env bash

set -ex

CAPW=`cat /tmp/ca_password`
USER_ARGS="server_ip=$LXC_IP server_user=ubuntu ssh_tunneling_enabled=y IP_subject=$LXC_IP easyrsa_CA_password=$CAPW apparmor_enabled=false install_headers=false"

sed -i 's/- jack$/- jack_test/' config.cfg

if [ "${LXC_NAME}" == "docker" ]
then
  docker run -it -v $(pwd)/config.cfg:/algo/config.cfg -v ~/.ssh:/root/.ssh -v $(pwd)/configs:/algo/configs -e "USER_ARGS=${USER_ARGS}" travis/algo /bin/sh -c "chown -R 0:0 /root/.ssh && source env/bin/activate && ansible-playbook users.yml -e \"${USER_ARGS}\" -t update-users --skip-tags common"
else
  ansible-playbook users.yml -e "${USER_ARGS}" -t update-users --skip-tags common
fi

if sudo openssl crl -inform pem -noout -text -in configs/$LXC_IP/pki/crl/jack.crt | grep CRL
  then
    echo "The CRL check passed"
  else
    echo "The CRL check failed"
    exit 1
fi

if sudo openssl x509 -inform pem -noout -text -in configs/$LXC_IP/pki/certs/jack_test.crt | grep CN=jack_test
  then
    echo "The new user exists"
  else
    echo "The new user does not exist"
    exit 1
fi
