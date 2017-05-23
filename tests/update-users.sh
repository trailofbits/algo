#!/usr/bin/env bash

set -ex

CAPW=`cat /tmp/ca_password`

sed -i 's/- jack$/- jack_test/' config.cfg

ansible-playbook users.yml -e "server_ip=$LXC_IP server_user=root ssh_tunneling_enabled=y IP_subject=$LXC_IP easyrsa_CA_password=$CAPW"

cd configs/$LXC_IP/pki/

if openssl crl -inform pem -noout -text -in crl/jack.crt | grep CRL
  then
    echo "The CRL check passed"
  else
    echo "The CRL check failed"
    exit 1
fi

if openssl x509 -inform pem -noout -text -in certs/jack_test.crt | grep CN=jack_test
  then
    echo "The new user exists"
  else
    echo "The new user does not exist"
    exit 1
fi
