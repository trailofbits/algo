#!/usr/bin/env bash

set -ex

DEPLOY_ARGS="server_ip=$LXC_IP server_user=root IP_subject_alt_name=$LXC_IP local_dns=Y"

if [ "${LXC_NAME}" == "docker" ]
then
  docker run -it -v $(pwd)/config.cfg:/algo/config.cfg -v ~/.ssh:/root/.ssh -e "DEPLOY_ARGS=${DEPLOY_ARGS}" travis/algo /bin/sh -c "chown -R 0:0 /root/.ssh && source env/bin/activate && ansible-playbook deploy.yml -t local,vpn,dns,ssh_tunneling,security,tests -e \"${DEPLOY_ARGS}\""
else
  ansible-playbook deploy.yml -t local,vpn,dns,ssh_tunneling,tests -e "${DEPLOY_ARGS}" -vvvv
fi
