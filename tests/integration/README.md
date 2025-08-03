# Docker Integration Tests

This directory contains Docker-based integration tests for Algo VPN. These tests use Docker containers to simulate a complete VPN deployment and test connectivity between server and clients.

## Overview

The integration tests use Docker Compose to:
1. Build an Algo server container
2. Provision it with a test configuration
3. Build client containers (Ubuntu, Debian)
4. Test VPN connections (WireGuard and IPsec)
5. Verify functionality like DNS resolution, routing, and multi-user support

## Architecture

```
┌─────────────────┐
│  algo-test      │  Docker Network (10.99.0.0/24)
│   network       │
└────────┬────────┘
         │
    ┌────┴────┬───────────┬──────────┐
    │         │           │          │
┌───▼───┐ ┌──▼────┐ ┌────▼───┐ ┌───▼────┐
│ Host  │ │ Algo  │ │ Ubuntu │ │ Debian │
│ (gw)  │ │Server │ │ Client │ │ Client │
│.0.1   │ │ .0.10 │ │  .0.20 │ │  .0.21 │
└───────┘ └───────┘ └────────┘ └────────┘
           │
           ├── WireGuard (10.19.49.0/24)
           └── IPsec (10.19.48.0/24)
```

## Running Tests Locally

### Prerequisites
- Docker and Docker Compose installed
- Python 3.8+ with pip
- At least 2GB free disk space

### Quick Start
```bash
cd tests/integration
./run-docker-tests.sh
```

### Running Specific Tests
```bash
# Run only WireGuard tests
python3 test_docker_vpn.py -k test_wireguard

# Run with verbose output
python3 test_docker_vpn.py -v

# Keep containers running after tests (for debugging)
python3 test_docker_vpn.py --no-cleanup
```

## Test Scenarios

### 1. WireGuard Connection Test
- Provisions Algo server with WireGuard enabled
- Configures client with generated WireGuard config
- Tests connectivity to VPN gateway
- Verifies DNS resolution through tunnel

### 2. IPsec Connection Test
- Provisions Algo server with IPsec/StrongSwan
- Configures client with certificates
- Tests IPsec tunnel establishment
- Note: Limited in containers due to kernel requirements

### 3. DNS Functionality Test
- Tests DNS resolution through VPN tunnel
- Verifies ad-blocking if enabled
- Checks for DNS leaks

### 4. Multiple Client Test
- Connects multiple clients simultaneously
- Verifies each client can reach the gateway
- Tests inter-client connectivity (based on BetweenClients_DROP)

### 5. Service Availability Test
- Checks all Algo services are running
- Verifies configuration files are generated
- Tests service health endpoints

## Debugging

### View Container Logs
```bash
docker logs algo-server
docker logs client-ubuntu
docker exec algo-server wg show
```

### Access Container Shell
```bash
docker exec -it algo-server bash
docker exec -it client-ubuntu bash
```

### Check Network Configuration
```bash
docker network inspect algo-test
docker exec client-ubuntu ip route
docker exec client-ubuntu wg show
```

## CI/CD Integration

The tests run automatically on:
- Pull requests that modify Algo code
- Weekly schedule (Monday 3 AM UTC)
- Manual workflow dispatch

Test artifacts (logs, configs) are uploaded for debugging failed runs.

## Limitations

1. **IPsec/StrongSwan**: Full IPsec testing is limited in containers due to kernel module requirements
2. **Performance**: Container networking adds overhead; not suitable for performance testing
3. **Platform-specific**: Some features may behave differently in containers vs real systems

## Adding New Tests

1. Add test method to `test_docker_vpn.py`
2. Use `self.docker_exec()` to run commands in containers
3. Follow naming convention: `test_<feature>_<scenario>`
4. Add appropriate assertions and error messages

Example:
```python
def test_my_new_feature(self):
    """Test description"""
    result = self.docker_exec("client-ubuntu", "command")
    self.assertEqual(result.returncode, 0)
    self.assertIn("expected output", result.stdout)
```