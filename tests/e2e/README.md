# End-to-End VPN Connectivity Tests

This directory contains end-to-end tests that verify actual VPN connectivity
using Linux network namespaces.

## Architecture

```
+---------------------------+     veth pair      +---------------------------+
|   Main Namespace          |                    |   Client Namespace        |
|   (VPN Server)            |                    |   (algo-client)           |
|                           |                    |                           |
|   wg0: 10.49.0.1         |   veth-algo-srv    |   veth-algo-cli           |
|   strongswan listening    |<----------------->|   10.99.0.2/24            |
|   dns: 172.16.0.1        |   10.99.0.1/24     |                           |
|                           |                    |   wg0 (after connection)  |
+---------------------------+                    +---------------------------+
```

The test creates a network namespace that simulates a VPN client. Traffic from
the namespace routes through a veth pair to the host, which NATs it to allow
the client to connect to the VPN server running on localhost.

## Running Locally (Linux)

These tests require Linux (network namespaces are a Linux kernel feature).

```bash
# Deploy Algo first
ansible-playbook main.yml -e "provider=local"

# Run all connectivity tests
sudo tests/e2e/test-vpn-connectivity.sh both

# Run only WireGuard tests
sudo tests/e2e/test-vpn-connectivity.sh wireguard

# Run only IPsec tests
sudo tests/e2e/test-vpn-connectivity.sh ipsec
```

## Running on macOS (via Multipass)

Use [Multipass](https://multipass.run/) to run an Ubuntu VM:

```bash
# Launch and mount algo directory
multipass launch 22.04 --name algo-test --cpus 2 --memory 4G --disk 20G
multipass mount ~/path/to/algo algo-test:/home/ubuntu/algo
multipass shell algo-test

# Inside VM: install dependencies and deploy
sudo apt-get update
sudo apt-get install -y python3-pip wireguard-tools strongswan libxml2-utils dnsutils
curl -LsSf https://astral.sh/uv/install.sh | sh && source ~/.bashrc
cd ~/algo && uv sync
uv run ansible-playbook main.yml -e "provider=local"

# Run tests
sudo tests/e2e/test-vpn-connectivity.sh both

# Cleanup (from macOS)
multipass delete algo-test && multipass purge
```

## Requirements

- Root access (for network namespace operations)
- Linux (network namespaces are a kernel feature)
- Deployed Algo VPN on localhost (configs in `configs/localhost/`)
- A user named `alice` in the config (default in CI; override with `TEST_USER=username`)
- Required tools:
  - `iproute2` (ip netns)
  - `wireguard-tools` (wg, wg-quick)
  - `strongswan` (ipsec, swanctl)
  - `libxml2-utils` (xmllint)
  - `openssl`
  - `dnsutils` (host)

## What Gets Tested

### Validation Tests (No Namespace Required)
- mobileconfig XML syntax validation (`xmllint`)
- CA certificate chain verification (`openssl verify`)

### WireGuard Tests
1. Client config file exists and is parseable
2. WireGuard interface comes up in namespace
3. Cryptographic handshake completes (checks `latest handshake`)
4. Ping to server VPN IP (10.49.0.1) succeeds
5. DNS resolution through VPN (172.16.0.1) works

### IPsec Tests
1. Certificate and key files exist
2. Certificate chain validates
3. IPsec service is running and listening
4. IPsec ports (500, 4500) are reachable
5. DNS service is responding

## Test Flow

1. **Setup**: Create `algo-client` network namespace with veth pair
2. **Validate**: Check mobileconfig XML and certificates
3. **WireGuard**: Start wg-quick in namespace, verify handshake and connectivity
4. **IPsec**: Verify certificates and service status
5. **Cleanup**: Remove namespace, NAT rules, and temp files

## Troubleshooting

### Common Issues

**Namespace already exists**
```bash
sudo ip netns del algo-client
```

**WireGuard handshake timeout**
- Check firewall allows UDP 51820
- Verify wg0 interface exists on host: `sudo wg show`
- Check server public key matches config

**IPsec connection failed**
- Verify strongswan service: `sudo systemctl status strongswan-starter`
- Check certificates: `openssl verify -CAfile cacert.pem user.crt`
- Review logs: `sudo journalctl -u strongswan -n 50`

**DNS resolution failed**
- Check dnscrypt-proxy: `sudo systemctl status dnscrypt-proxy`
- Verify DNS IP is routed: `ip route get 172.16.0.1`
- Test from host: `host google.com 172.16.0.1`

### Debug Mode

If tests fail, debug information is automatically collected including:
- Network interfaces and routes
- WireGuard and IPsec status
- iptables NAT rules
- DNS service status
- Recent system logs

## CI Integration

These tests run automatically in GitHub Actions after Algo deployment:

```yaml
- name: Run E2E VPN connectivity tests
  run: sudo tests/e2e/test-vpn-connectivity.sh "${{ matrix.vpn_type }}"
```

The tests are matrix-aware and run for `wireguard`, `ipsec`, or `both`
configurations.
