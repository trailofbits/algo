# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Algo VPN is an Ansible-based project that automates the setup of secure personal WireGuard and IPsec VPN servers on various cloud providers. It uses strong cryptographic defaults and supports multiple deployment targets including DigitalOcean, AWS, Google Cloud, Azure, and others.

## Development Commands

### Core Setup and Deployment

- **Setup environment**: `make install` - Install Ansible dependencies and development tools
- **Deploy VPN server**: `./algo` or `make deploy` - Interactive deployment script that runs the main Ansible playbook
- **Update users**: `./algo update-users` or `make update-users` - Add/remove users from existing VPN servers (requires retained PKI)

### Testing

- **Run all tests**: Tests are located in `tests/` directory with individual scripts for different scenarios:
  - `tests/wireguard-client.sh` - Test WireGuard client functionality
  - `tests/ipsec-client.sh` - Test IPsec client functionality
  - `tests/ssh-tunnel.sh` - Test SSH tunneling
  - `tests/local-deploy.sh` - Test local deployment
  - `tests/update-users.sh` - Test user management

### Linting and Validation

- **Quick linting**: `make lint` - Run pre-commit hooks on all files
- **Comprehensive linting**: `make lint-full` - Pre-commit + Ansible + shell script checks
- **Auto-fix linting**: `make lint-fix` - Apply automatic fixes where possible
- **Manual checks**:
  - Syntax check: `ansible-playbook main.yml --syntax-check`
  - Shell script linting: `shellcheck algo install.sh`
  - Ansible linting: `ansible-lint *.yml roles/{local,cloud-*}/*/*.yml`

### Docker Operations

- **Build Docker image**: `make docker-build` or `docker build -t trailofbits/algo .`
- **Deploy via Docker**: `make docker-deploy`
- **Clean Docker images**: `make docker-prune`

## Architecture

### Core Structure

- **Main playbooks**:
  - `main.yml` - Primary deployment playbook with requirements verification
  - `users.yml` - User management for existing servers
  - `server.yml` - Server configuration tasks

### Ansible Roles

- **Cloud providers**: `cloud-*` roles handle provisioning for different providers (AWS, GCP, Azure, DigitalOcean, etc.)
- **VPN protocols**:
  - `wireguard/` - WireGuard server and client configuration
  - `strongswan/` - IPsec/IKEv2 with strongSwan implementation
- **Core services**:
  - `common/` - Base system configuration, firewall rules, updates
  - `dns/` - DNS resolver with optional ad-blocking via dnscrypt-proxy
  - `ssh_tunneling/` - Optional SSH tunnel configuration
  - `client/` - Client-side installation tasks

### Configuration

- **Main config**: `config.cfg` - YAML file containing all deployment options including:
  - User list for VPN access
  - Cloud provider settings
  - VPN protocol configuration (WireGuard/IPsec)
  - DNS and security options
- **Ansible config**: `ansible.cfg` - Ansible execution settings

### Generated Outputs

- **Client configs**: `configs/<server_ip>/` directory contains:
  - `wireguard/<user>.conf` - WireGuard configuration files
  - `wireguard/<user>.png` - QR codes for mobile setup
  - `ipsec/` - IPsec certificates and configuration
  - SSH keys and configuration for tunneling

### Key Files

- `algo` script - Main entry point that activates virtual environment and runs appropriate playbook
- `requirements.txt` - Python dependencies (Ansible, Jinja2, netaddr)
- `install.sh` - Installation script for dependencies
- `inventory` - Ansible inventory file

## Quantum-Safe Development

This repository now includes quantum-safe cryptography capabilities in development:

### Quantum-Safe Commands

- **Setup quantum-safe environment**: `ansible-playbook quantum-safe-dev.yml`
- **Run quantum-safe tests**: `/opt/quantum-safe/tests/run-all-tests.sh`
- **Performance benchmarks**: `/opt/quantum-safe/tests/benchmark-quantum-safe.sh`

### Post-Quantum Cryptography

- **liboqs integration**: ML-KEM and ML-DSA algorithms (NIST standardized)
- **strongSwan enhancement**: Hybrid classical + post-quantum configurations
- **Testing infrastructure**: Comprehensive validation and performance monitoring
- **Phase 1 complete**: Research and development environment established

### Quantum-Safe Architecture

- `roles/quantum-safe/` - Ansible role for post-quantum library management
- `docs/quantum-safe-architecture.md` - Architectural decisions and implementation guide
- `docs/phase1-research-summary.md` - Complete Phase 1 analysis and findings

## Important Notes

- Python 3.10+ required
- Deployment requires cloud provider API credentials
- PKI retention is necessary for user management after initial deployment
- VPN uses strong crypto defaults: AES-GCM, SHA2, P-256 for IPsec; ChaCha20-Poly1305 for WireGuard
- **Quantum-safe mode**: Hybrid classical + post-quantum algorithms available (development)
- Ad-blocking DNS is optional but enabled by default
- All generated certificates and keys are stored in `configs/` directory
