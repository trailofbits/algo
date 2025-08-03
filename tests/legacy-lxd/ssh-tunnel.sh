#!/usr/bin/env bash

set -euxo pipefail

PASS=$(grep ^p12_password: configs/10.0.8.100/.config.yml | awk '{print $2}' | cut -f2 -d\')

ssh-keygen -p -P ${PASS} -N '' -f configs/10.0.8.100/ssh-tunnel/desktop.pem

ssh -o StrictHostKeyChecking=no -D 127.0.0.1:1080 -f -q -C -N desktop@10.0.8.100 -i configs/10.0.8.100/ssh-tunnel/desktop.pem -F configs/10.0.8.100/ssh_config

git config --global http.proxy 'socks5://127.0.0.1:1080'

for i in {1..10}; do git clone -vv https://github.com/trailofbits/algo /tmp/ssh-tunnel-check && break || sleep 1; done

echo "SSH tunneling tests passed"
