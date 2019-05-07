#!/usr/bin/env bash

set -euxo pipefail

xmllint --noout ./configs/10.0.8.100/ipsec/apple/user1.mobileconfig

ansible-playbook deploy_client.yml \
  -e client_ip=localhost \
  -e vpn_user=desktop \
  -e server_ip=10.0.8.100 \
  -e rightsubnet='172.16.0.1/32'

ipsec up algovpn-10.0.8.100

ipsec statusall

ipsec statusall | grep -w ^algovpn-10.0.8.100 | grep -w ESTABLISHED

fping -t 900 -c3 -r3 -Dse 10.0.8.100 172.16.0.1

host google.com 172.16.0.1

echo "IPsec tests passed"

ipsec down algovpn-10.0.8.100
