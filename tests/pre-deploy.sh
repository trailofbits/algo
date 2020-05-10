#!/usr/bin/env bash

set -euxo pipefail

sysctl net.ipv6.conf.all.disable_ipv6=0

tar xf $HOME/lxc/cache.tar -C / || echo "Didn't extract cache."
cp -f tests/lxd-bridge /etc/default/lxd-bridge
cp -f tests/algo.conf /etc/default/algo.conf

export REPOSITORY=${REPOSITORY:-${GITHUB_REPOSITORY}}
export _BRANCH=${BRANCH#refs/heads/}
export BRANCH=${_BRANCH:-${GITHUB_REF#refs/heads/}}

if [[ "$DEPLOY" == "cloud-init" ]]; then
  bash tests/cloud-init.sh | lxc profile set default user.user-data -
else
  echo -e "#cloud-config\nssh_authorized_keys:\n - $(cat ~/.ssh/id_rsa.pub)" | lxc profile set default user.user-data -
fi

systemctl restart lxd-bridge.service lxd-containers.service lxd.service

lxc profile set default raw.lxc lxc.aa_profile=unconfined
lxc profile set default security.privileged true
lxc profile show default
lxc launch ubuntu:${UBUNTU_VERSION} algo

if [[ ${UBUNTU_VERSION} == "20.04" ]]; then
  lxc exec algo -- apt remove snapd --purge -y || true
fi

ip addr

until dig A +short algo.lxd @10.0.8.1 | grep -vE '^$' > /dev/null; do
  sleep 3
done

lxc list
