#!/bin/bash
# Simple test that verifies Algo can generate configurations without errors

set -e

echo "Testing Algo configuration generation..."

# Generate SSH key if it doesn't exist
if [ ! -f ~/.ssh/id_rsa ]; then
    ssh-keygen -f ~/.ssh/id_rsa -t rsa -N ''
fi

# Create a minimal test configuration
cat > test-config.cfg << 'EOF'
users:
  - test-user
cloud_providers:
  local:
    server: localhost
    endpoint: 127.0.0.1
wireguard_enabled: true
ipsec_enabled: false
dns_adblocking: false
ssh_tunneling: false
store_pki: true
tests: true
algo_provider: local
algo_server_name: test-server
algo_ondemand_cellular: false
algo_ondemand_wifi: false
algo_ondemand_wifi_exclude: ""
algo_dns_adblocking: false
algo_ssh_tunneling: false
wireguard_PersistentKeepalive: 0
wireguard_network: 10.19.49.0/24
wireguard_network_ipv6: fd9d:bc11:4020::/48
wireguard_port: 51820
dns_encryption: false
subjectAltName_type: IP
subjectAltName: 127.0.0.1
IP_subject_alt_name: 127.0.0.1
algo_server: localhost
algo_user: ubuntu
ansible_ssh_user: ubuntu
algo_ssh_port: 22
endpoint: 127.0.0.1
server: localhost
ssh_user: ubuntu
CA_password: "test-password-123"
p12_export_password: "test-export-password"
EOF

# Run Ansible in check mode to verify templates work
echo "Running Ansible in check mode..."
uv run ansible-playbook main.yml \
    -i "localhost," \
    -c local \
    -e @test-config.cfg \
    -e "provider=local" \
    --check \
    --diff \
    --tags "configuration" \
    --skip-tags "restart_services,tests,assert,cloud,facts_install"

echo "Configuration generation test passed!"

# Clean up
rm -f test-config.cfg