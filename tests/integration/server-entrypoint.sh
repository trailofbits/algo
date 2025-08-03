#!/bin/bash
set -e

echo "Starting Algo server container..."

# Load kernel modules if needed
modprobe wireguard || true
modprobe af_key || true

# Install enhanced mock commands
cp /algo/tests/integration/mock-systemctl.sh /usr/bin/systemctl
cp /algo/tests/integration/mock-service.sh /usr/bin/service
chmod +x /usr/bin/systemctl /usr/bin/service

# Initialize some services as "running" to simulate a real system
mkdir -p /var/lib/fake-systemd
touch /var/lib/fake-systemd/systemd-resolved.active
touch /var/lib/fake-systemd/systemd-resolved.enabled
touch /var/lib/fake-systemd/systemd-networkd.active
touch /var/lib/fake-systemd/systemd-networkd.enabled

# Create mock service files so Ansible's systemd module finds them
mkdir -p /etc/systemd/system /lib/systemd/system
for service in systemd-networkd systemd-resolved netfilter-persistent apparmor \
               wg-quick@wg0 strongswan-starter ipsec unattended-upgrades; do
    cat > /lib/systemd/system/${service}.service << EOF
[Unit]
Description=Mock ${service} service

[Service]
Type=simple
ExecStart=/bin/true

[Install]
WantedBy=multi-user.target
EOF
done

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
wireguard_network_ipv4: 10.19.49.0/24
wireguard_network_ipv6: fd9d:bc11:4020::/64
wireguard_port: 51820
wireguard_PersistentKeepalive: 0

strongswan_network: 10.19.48.0/24
strongswan_network_ipv4: 10.19.48.0/24
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

# Local service IP (gateway for wireguard network)
local_service_ip: 10.19.49.1
local_service_ipv6: 2001:db8:a160::1

# Other settings
algo_ondemand_cellular: false
algo_ondemand_wifi: false
algo_ssh_tunneling: false
algo_store_pki: true
BetweenClients_DROP: false
block_smb: true
block_netbios: true
pki_in_tmpfs: false
ansible_connection: local
ansible_python_interpreter: /usr/bin/python3
server_user: root
CA_password: test_ca_password_123
p12_export_password: test_p12_password_123
unattended_reboot:
  enabled: false
  time: 04:00
ssh_port: 22
algo_ssh_port: 4160
reduce_mtu: 0
keepalive_timeout: 600
tests: false
no_log: false
alternative_ingress_ip: false
install_headers: false
apparmor_enabled: false
strongswan_log_level: 1
congrats:
  common: |
    "#                          Congratulations!                            #"
    "#                     Your Algo server is running.                     #"
    "#    Config files and certificates are in the ./configs/ directory.    #"
  playbook: |
    "#                          Congratulations!                            #"
    "#                    Your Algo VPN server is ready!                    #"
  p12_pass: |
    "#        The p12 and SSH keys password for new users is drkf3bnaM     #"
  ca_key_pass: |
    "#     The CA key password is 6Uyy3RrotOtYIaD2                         #"
  ssh_access: ""
EOF

# Run Algo provisioning
cd /algo
echo "Running Algo provisioning..."

# Create dummy sshd pam file to avoid errors
mkdir -p /etc/pam.d
touch /etc/pam.d/sshd

# Update apt cache to prevent issues later
apt-get update || true

# Use our mock Ansible modules
export ANSIBLE_LIBRARY=/algo/tests/integration/mock_modules

ansible-playbook main.yml \
    -e @config.cfg \
    -e "provider=local" \
    -e "server=localhost" \
    -e "endpoint=10.99.0.10" \
    -e "ansible_default_ipv4.address=10.99.0.10" \
    -e "ansible_default_ipv4.interface=eth0" \
    --skip-tags "reboot,ssh_tunneling" \
    -v

# Mark as provisioned
touch /etc/algo/.provisioned

# Copy generated configs to shared volume
cp -r /algo/configs/* /etc/algo/ || true

echo "Algo server provisioned successfully"

# Start services that would normally be started by systemd
echo "Starting VPN services..."

# Start StrongSwan if configured
if [ -f /etc/ipsec.conf ]; then
    echo "Starting StrongSwan..."
    ipsec start || true
fi

# Start WireGuard interfaces if configured
if [ -d /etc/wireguard ]; then
    for conf in /etc/wireguard/*.conf; do
        if [ -f "$conf" ]; then
            interface=$(basename "$conf" .conf)
            echo "Starting WireGuard interface: $interface"
            wg-quick up "$interface" || true
        fi
    done
fi

# Keep container running
tail -f /dev/null