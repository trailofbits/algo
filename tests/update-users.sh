#!/usr/bin/env bash

set -ex

USER_ARGS="{ 'server': '$LXC_IP', 'users': ['user1', 'user2'] }"

if [ "${LXC_NAME}" == "docker" ]
then
  docker run -it -v $(pwd)/config.cfg:/algo/config.cfg -v ~/.ssh:/root/.ssh -v $(pwd)/configs:/algo/configs -e "USER_ARGS=${USER_ARGS}" travis/algo /bin/sh -c "chown -R 0:0 /root/.ssh && source env/bin/activate && ansible-playbook users.yml -e \"${USER_ARGS}\" -t update-users"
else
  ansible-playbook users.yml -e "${USER_ARGS}" -t update-users
fi

if sudo openssl crl -inform pem -noout -text -in configs/$LXC_IP/pki/crl/jack.crt | grep CRL
  then
    echo "The CRL check passed"
  else
    echo "The CRL check failed"
    exit 1
fi

if sudo openssl x509 -inform pem -noout -text -in configs/$LXC_IP/pki/certs/user1.crt | grep CN=user1
  then
    echo "The new user exists"
  else
    echo "The new user does not exist"
    exit 1
fi
