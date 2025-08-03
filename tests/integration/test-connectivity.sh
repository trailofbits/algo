#!/bin/bash
set -e

echo "Testing connectivity between clients and server..."

# Test that client containers can ping the server
echo "Testing client-ubuntu connectivity..."
docker-compose exec -T client-ubuntu ping -c 3 10.99.0.10

echo "Testing client-debian connectivity..."
docker-compose exec -T client-debian ping -c 3 10.99.0.10

# Future: Add actual VPN connectivity tests here
# This would involve:
# 1. Copying generated configs to client containers
# 2. Establishing VPN connections
# 3. Testing connectivity through the VPN tunnel

echo "Basic connectivity tests passed!"