#!/usr/bin/env bash

set -ex

CAPW=`cat /tmp/ca_password`
USER_ARGS="server_ip=$LXC_IP easyrsa_CA_password=$CAPW users=['user1', 'user2']"
USERS=""

if [ "${LXC_NAME}" == "docker" ]
then
  docker run -it -v $(pwd)/config.cfg:/algo/config.cfg -v ~/.ssh:/root/.ssh -e "USER_ARGS=${USER_ARGS}" travis/algo /bin/sh -c "chown -R 0:0 /root/.ssh && source env/bin/activate && ansible-playbook users.yml -e \"${USER_ARGS}\""
else
  ansible-playbook users.yml -e "${USER_ARGS}"
fi

cd configs/$LXC_IP/pki/

if openssl crl -inform pem -noout -text -in crl/jack.crt | grep CRL
  then
    echo "The CRL check passed"
  else
    echo "The CRL check failed"
    exit 1
fi

if openssl x509 -inform pem -noout -text -in certs/user1.crt | grep CN=user1
  then
    echo "The new user exists"
  else
    echo "The new user does not exist"
    exit 1
fi
