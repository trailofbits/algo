#!/bin/bash
set -e

echo "=== Algo Docker Integration Tests ==="
echo "This will test VPN connectivity using Docker containers"
echo ""

# Check Docker is available
if ! command -v docker &> /dev/null; then
    echo "ERROR: Docker is not installed"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "ERROR: docker-compose is not installed"
    exit 1
fi

# Change to integration test directory
cd "$(dirname "$0")"

# Clean up any existing containers
echo "Cleaning up existing containers..."
docker-compose down -v 2>/dev/null || true

# Run the tests
echo "Starting integration tests..."
python3 test_docker_vpn.py "$@"

# Clean up
echo "Cleaning up..."
docker-compose down -v