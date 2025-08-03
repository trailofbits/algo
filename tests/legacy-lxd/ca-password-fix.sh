#!/usr/bin/env bash

# Refer PR #1774 for more details.

set -ex

DEPLOY_ARGS="provider=local server=10.0.8.100 ssh_user=ubuntu endpoint=10.0.8.100 ondemand_cellular=true ondemand_wifi=true ondemand_wifi_exclude=test dns_adblocking=true ssh_tunneling=true store_pki=true install_headers=false tests=true local_service_ip=172.16.0.1 no_log=false"

CA_PASSWORD="test123"

if [ "${DEPLOY}" == "docker" ]
then
  docker run -i -v $(pwd)/config.cfg:/algo/config.cfg -v ~/.ssh:/root/.ssh -v $(pwd)/configs:/algo/configs -e "DEPLOY_ARGS=${DEPLOY_ARGS}" local/algo /bin/sh -c "chown -R root: /root/.ssh && chmod -R 600 /root/.ssh && source .env/bin/activate && ansible-playbook main.yml -e \"${DEPLOY_ARGS}\" --skip-tags debug"
else
  ansible-playbook main.yml -e "${DEPLOY_ARGS} ca_password=${CA_PASSWORD}"
fi

CA_PASSWORD_OUT=$(grep ca_password: configs/localhost/.config.yml | awk '{print $2}' | xargs)

if [ "$CA_PASSWORD" = "$CA_PASSWORD_OUT" ]; then
  echo "ca_password tests(PR #1774) passed"
else
  echo "ca_password tests(PR #1774) failed"
  exit 1
fi
