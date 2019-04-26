#!/usr/bin/env bash

set -euxo pipefail

PASS=$(grep ^p12_password: configs/10.0.8.100/.config.yml | awk '{print $2}')

ssh-keygen -p -P ${PASS} -N '' -f configs/10.0.8.100/ssh-tunnel/desktop.pem

ssh -o StrictHostKeyChecking=no -D 127.0.0.1:1080 -f -q -C -N desktop@10.0.8.100 -i configs/10.0.8.100/ssh-tunnel/desktop.pem

git config --global http.proxy 'socks5://127.0.0.1:1080'

git clone -vv https://github.com/trailofbits/algo /tmp/ssh-tunnel-check

echo "SSH tunneling tests passed"
