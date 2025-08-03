#!/bin/bash
set -e

echo "Building Docker images..."
docker-compose build

echo "Starting test environment..."
docker-compose up -d algo-server

echo "Waiting for Algo server to provision..."
max_wait=300
wait_time=0
while [ ! -f "configs/.provisioned" ] && [ $wait_time -lt $max_wait ]; do
    echo "Waiting for provisioning to complete... ($wait_time/$max_wait seconds)"
    sleep 10
    wait_time=$((wait_time + 10))
    
    # Check if container is still running
    if ! docker-compose ps algo-server | grep -q "Up"; then
        echo "ERROR: Algo server container stopped unexpectedly"
        echo "Container logs:"
        docker-compose logs algo-server
        exit 1
    fi
done

if [ ! -f "configs/.provisioned" ]; then
    echo "ERROR: Provisioning did not complete within $max_wait seconds"
    echo "Container logs:"
    docker-compose logs algo-server
    exit 1
fi

echo "Algo server provisioned successfully!"

echo "Starting client containers..."
docker-compose up -d client-ubuntu client-debian

echo "Running connectivity tests..."
./test-connectivity.sh

echo "All tests passed!"