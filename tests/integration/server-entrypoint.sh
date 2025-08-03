#!/bin/bash
set -e

echo "Starting Algo server container..."

# Load kernel modules if needed
modprobe wireguard || true
modprobe af_key || true

# Create test configuration
cat > /algo/config.cfg << EOF
users:
  - testuser1
  - testuser2

cloud_providers:
  local:
    server: algo-server
    endpoint: 10.99.0.10

wireguard_enabled: true
ipsec_enabled: true
dns_adblocking: false
ssh_tunneling: false
store_pki: true

algo_provider: local
algo_server_name: algo-test-server
server: 10.99.0.10
IP_subject_alt_name: 10.99.0.10

# Network configuration
ipv4_network_prefix: 10.19.49
ipv6_network: fd9d:bc11:4020::/48
wireguard_network: 10.19.49.0/24
wireguard_network_ipv6: fd9d:bc11:4020::/64
wireguard_port: 51820
wireguard_PersistentKeepalive: 0

strongswan_network: 10.19.48.0/24
strongswan_network_ipv6: fd9d:bc11:4021::/64

# DNS
dns_encryption: false
dns_servers:
  ipv4:
    - 8.8.8.8
    - 8.8.4.4
  ipv6:
    - 2001:4860:4860::8888
    - 2001:4860:4860::8844

# Other settings
algo_ondemand_cellular: false
algo_ondemand_wifi: false
algo_ssh_tunneling: false
algo_store_pki: true
BetweenClients_DROP: false
block_smb: true
block_netbios: true
EOF

# Run Algo provisioning
cd /algo
echo "Running Algo provisioning..."
ansible-playbook main.yml \
    -e "provider=local" \
    -e "server=localhost" \
    -e "endpoint=10.99.0.10" \
    -e "ondemand_cellular=false" \
    -e "ondemand_wifi=false" \
    -e "dns_adblocking=false" \
    -e "ssh_tunneling=false" \
    -e "store_pki=true" \
    --skip-tags "reboot,facts" \
    -v

# Mark as provisioned
touch /etc/algo/.provisioned

# Copy generated configs to shared volume
cp -r /algo/configs/* /etc/algo/ || true

echo "Algo server provisioned successfully"

# Keep container running
tail -f /dev/null