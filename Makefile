# Algo Quantum VPN Makefile
# Enhanced with quantum-safe development workflow

.PHONY: help install clean lint test build docker-build docker-deploy docker-prune docker-all setup-dev release all check

# Default target
all: clean install lint-full test build ## Full pipeline - clean, install, lint, test, build
help: ## Show this help message
	@echo 'Usage: make [TARGET] [EXTRA_ARGUMENTS]'
	@echo 'Targets:'
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# Variables
IMAGE          := trailofbits/algo
TAG	  	       := latest
DOCKERFILE     := Dockerfile
CONFIGURATIONS := $(shell pwd)
PYTHON         := python3
VENV_DIR       := .env

## Development Setup
install: ## Install dependencies and set up development environment
	@echo "Setting up Algo VPN development environment..."
	@echo "Installing Python dependencies..."
	$(PYTHON) -m pip install --user -r requirements.txt
	$(PYTHON) -m pip install --user pre-commit ansible-lint yamllint
	@echo "Installing pre-commit hooks..."
	pre-commit install
	@echo "Development environment ready!"

setup-dev: install ## Alias for install

clean: ## Clean up generated files
	rm -rf .pytest_cache
	rm -rf __pycache__
	rm -rf .coverage
	rm -rf releases/
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete

## Linting and Code Quality
lint: ## Run pre-commit hooks on all files
	@echo "Running pre-commit hooks on all files..."
	pre-commit run --all-files

lint-full: ## Run comprehensive linting (pre-commit + Ansible + shell checks)
	@echo "Running pre-commit hooks on all files..."
	pre-commit run --all-files
	@echo "Running Ansible syntax check..."
	ansible-playbook main.yml --syntax-check
	ansible-playbook users.yml --syntax-check
	@echo "Running shell script checks..."
	shellcheck algo install.sh scripts/*.sh
	find tests/ -name "*.sh" -exec shellcheck {} \;

lint-fix: ## Run linting with auto-fix where possible
	pre-commit run --all-files

## Testing
test: ## Run tests
	@echo "Running Ansible playbook syntax validation..."
	ansible-playbook main.yml --syntax-check
	ansible-playbook users.yml --syntax-check
	@echo "Running shell script tests..."
	@if [ -f "tests/run_tests.sh" ]; then \
		bash tests/run_tests.sh; \
	else \
		echo "No test runner found - individual test scripts available in tests/"; \
	fi

## Building
build: lint-full test ## Build and validate the project
	@echo "Project built and validated successfully!"

## Docker Operations
docker-build: ## Build and tag a docker image
	docker build \
	-t $(IMAGE):$(TAG) \
	-f $(DOCKERFILE) \
	.

docker-deploy: ## Mount config directory and deploy Algo
	# '--rm' flag removes the container when finished.
	docker run \
	--cap-drop=all \
	--rm \
	-it \
	-v $(CONFIGURATIONS):/data \
	$(IMAGE):$(TAG)

docker-prune: ## Remove images and containers
	docker images \
	$(IMAGE) |\
	awk '{if (NR>1) print $$3}' |\
	xargs docker rmi

docker-all: docker-build docker-deploy docker-prune ## Build, Deploy, Prune

## Release Management
release: ## Create a new release (usage: make release VERSION=1.0.0)
	@if [ -z "$(VERSION)" ]; then \
		echo "Error: VERSION is required. Usage: make release VERSION=1.0.0"; \
		exit 1; \
	fi
	./scripts/create_release.sh $(VERSION)

release-push: ## Create and push a new release (usage: make release-push VERSION=1.0.0)
	@if [ -z "$(VERSION)" ]; then \
		echo "Error: VERSION is required. Usage: make release-push VERSION=1.0.0"; \
		exit 1; \
	fi
	./scripts/create_release.sh --push $(VERSION)

## Algo VPN Operations
deploy: ## Deploy Algo VPN (interactive)
	./algo

update-users: ## Update VPN users
	./algo update-users

## Development Shortcuts
dev-setup: install ## Set up development environment with all tools
	@echo "Installing additional development tools..."
	$(PYTHON) -m pip install --user black flake8 bandit

check: lint test ## Quick check - run linting and tests
