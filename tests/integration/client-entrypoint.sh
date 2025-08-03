#!/bin/bash
set -e

echo "Starting client container..."

# Wait for server to be ready
echo "Waiting for Algo server to be provisioned..."
while [ ! -f /etc/algo/.provisioned ]; do
    echo "Waiting for server provisioning..."
    sleep 10
done

echo "Server is ready!"

# Keep container running for testing
tail -f /dev/null