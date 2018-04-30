#!/usr/bin/env bash

set -ex

DEPLOY_ARGS="provider=local server=$LXC_IP ssh_user=ubuntu endpoint=$LXC_IP apparmor_enabled=false ondemand_cellular=true ondemand_wifi=true ondemand_wifi_exclude=test local_dns=true ssh_tunneling=true windows=true store_cakey=true install_headers=false tests=true"

if [ "${LXC_NAME}" == "docker" ]
then
  docker run -it -v $(pwd)/config.cfg:/algo/config.cfg -v ~/.ssh:/root/.ssh -v $(pwd)/configs:/algo/configs -e "DEPLOY_ARGS=${DEPLOY_ARGS}" travis/algo /bin/sh -c "chown -R 0:0 /root/.ssh && source env/bin/activate && ansible-playbook main.yml -e \"${DEPLOY_ARGS}\" --skip-tags apparmor"
else
  ansible-playbook main.yml -e "${DEPLOY_ARGS}" --skip-tags apparmor
fi
