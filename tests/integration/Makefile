# Makefile for Algo Docker Integration Tests

.PHONY: all build test clean logs shell-server shell-client help

# Default target
all: test

# Build Docker images
build:
	@echo "Building Docker images..."
	docker-compose build --parallel

# Run all tests
test: build
	@echo "Running integration tests..."
	python3 test_docker_vpn.py -v

# Run specific test
test-one: build
	@echo "Running test: $(TEST)"
	python3 test_docker_vpn.py -v -k $(TEST)

# Clean up Docker resources
clean:
	@echo "Cleaning up Docker resources..."
	docker-compose down -v --remove-orphans
	rm -rf test-configs
	rm -rf logs

# View logs from containers
logs:
	@echo "=== Algo Server Logs ==="
	@docker logs algo-server 2>&1 | tail -50
	@echo "\n=== Client Ubuntu Logs ==="
	@docker logs client-ubuntu 2>&1 | tail -20
	@echo "\n=== Client Debian Logs ==="
	@docker logs client-debian 2>&1 | tail -20

# Shell access to containers
shell-server:
	docker exec -it algo-server bash

shell-client:
	docker exec -it client-ubuntu bash

# Start containers without running tests
up:
	docker-compose up -d
	@echo "Waiting for Algo server to provision..."
	@while ! docker exec algo-server test -f /etc/algo/.provisioned 2>/dev/null; do \
		echo -n "."; \
		sleep 5; \
	done
	@echo "\nAlgo server ready!"

# Stop containers
down:
	docker-compose down

# Show container status
status:
	@docker-compose ps
	@echo "\n=== WireGuard Status ==="
	@docker exec algo-server wg show 2>/dev/null || echo "WireGuard not configured"

# Help
help:
	@echo "Algo Docker Integration Tests"
	@echo ""
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@echo "  test          - Build and run all integration tests"
	@echo "  test-one TEST=name - Run specific test by name"
	@echo "  build         - Build Docker images only"
	@echo "  up            - Start containers without tests"
	@echo "  down          - Stop containers"
	@echo "  clean         - Remove all containers and test data"
	@echo "  logs          - Show recent container logs"
	@echo "  status        - Show container and VPN status"
	@echo "  shell-server  - Open shell in server container"
	@echo "  shell-client  - Open shell in client container"
	@echo ""
	@echo "Examples:"
	@echo "  make test"
	@echo "  make test-one TEST=test_wireguard"
	@echo "  make shell-server"