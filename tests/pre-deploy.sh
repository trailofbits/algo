#!/usr/bin/env bash

set -euxo pipefail

sysctl net.ipv6.conf.all.disable_ipv6=0

export REPOSITORY=${REPOSITORY:-${GITHUB_REPOSITORY}}
export _BRANCH=${BRANCH#refs/heads/}
export BRANCH=${_BRANCH:-${GITHUB_REF#refs/heads/}}

if [[ "$DEPLOY" == "cloud-init" ]]; then
  bash tests/cloud-init.sh | lxc profile set default user.user-data -
else
  echo -e "#cloud-config\nssh_authorized_keys:\n - $(cat ~/.ssh/id_rsa.pub)" | lxc profile set default user.user-data -
fi

lxc network set lxdbr0 ipv4.address 10.0.8.1/24

lxc profile set default raw.lxc 'lxc.apparmor.profile = unconfined'
lxc profile set default security.privileged true
lxc profile show default

lxc init ubuntu:${UBUNTU_VERSION} algo
lxc network attach lxdbr0 algo eth0 eth0
lxc config device set algo eth0 ipv4.address 10.0.8.100
lxc start algo

ip addr

until dig A +short algo.lxd @10.0.8.1 | grep -vE '^$' > /dev/null; do
  sleep 3
done

case ${UBUNTU_VERSION} in
  20.04|22.04)
    lxc exec algo -- apt remove snapd --purge -y || true
    ;;
  18.04)
    lxc exec algo -- apt install python3.8 -y
    ;;
esac

lxc list
