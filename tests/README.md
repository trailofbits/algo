# Algo VPN Test Suite

## Current Test Coverage

### What We Test Now
1. **Basic Sanity** (`test_basic_sanity.py`)
   - Python version >= 3.10
   - requirements.txt exists
   - config.cfg is valid YAML
   - Ansible playbook syntax
   - Shell scripts pass shellcheck
   - Dockerfile exists and is valid

2. **Docker Build** (`test_docker_build.py`)
   - Docker image builds successfully
   - Container can start
   - Ansible is available in container

3. **Configuration Generation** (`test-local-config.sh`)
   - Ansible templates render without errors
   - Basic configuration can be generated

4. **Config Validation** (`test_config_validation.py`)
   - WireGuard config format validation
   - Base64 key format checking
   - IP address and CIDR notation
   - Mobile config XML validation
   - Port range validation

5. **Certificate Validation** (`test_certificate_validation.py`)
   - OpenSSL availability
   - Certificate subject formats
   - Key file permissions (600)
   - Password complexity
   - IPsec cipher suite security

6. **User Management** (`test_user_management.py`) - Addresses #14745, #14746, #14738, #14726
   - User list parsing from config
   - Server selection string parsing
   - SSH key preservation
   - CA password handling
   - User config path generation
   - Duplicate user detection

7. **OpenSSL Compatibility** (`test_openssl_compatibility.py`) - Addresses #14755, #14718
   - OpenSSL version detection
   - Legacy flag support detection
   - Apple device key format compatibility
   - Certificate generation compatibility
   - PKCS#12 export for mobile devices

8. **Docker Integration Tests** (`integration/test_docker_vpn.py`)
   - Full VPN server deployment in containers
   - WireGuard client connectivity testing
   - IPsec/StrongSwan tunnel testing
   - DNS resolution through VPN
   - Multiple client connections
   - Network isolation verification

9. **Cloud Provider Configs** (`test_cloud_provider_configs.py`) - Addresses #14752, #14730, #14762
   - Cloud provider configuration validation
   - Hetzner server type updates (cx11 → cx22)
   - Azure dependency compatibility
   - Region format validation
   - Server size naming conventions
   - OS image naming validation

10. **Template Rendering** (`test_template_rendering.py`)
    - Jinja2 template syntax validation
    - Variable substitution testing
    - Template security (no arbitrary code execution)
    - Configuration file generation

11. **Generated Configs** (`test_generated_configs.py`)
    - WireGuard config file validation
    - IPsec/StrongSwan config validation
    - DNS configuration validation
    - Firewall rules validation

### What We DON'T Test Yet

#### 1. VPN Functionality
- **WireGuard configuration validation**
  - Private/public key generation
  - Client config file format
  - QR code generation
  - Mobile config profiles
- **IPsec configuration validation**
  - Certificate generation and validation
  - StrongSwan config format
  - Apple profile generation
- **SSH tunnel configuration**
  - Key generation
  - SSH config file format

#### 2. Cloud Provider Integrations
- DigitalOcean API interactions
- AWS EC2/Lightsail deployments
- Azure deployments
- Google Cloud deployments
- Other providers (Vultr, Hetzner, etc.)

#### 3. User Management
- Adding new users
- Removing users
- Updating user configurations

#### 4. Advanced Features
- DNS ad-blocking configuration
- On-demand VPN settings
- MTU calculations
- IPv6 configuration

#### 5. Security Validations
- Certificate constraints
- Key permissions
- Password generation
- Firewall rules

## Potential Improvements

### Short Term (Easy Wins)
1. **Add job names** to fix zizmor warnings
2. **Test configuration file generation** without deployment:
   ```python
   def test_wireguard_config_format():
       # Generate a test config
       # Validate it has required sections
       # Check key format with regex
   ```

3. **Test user management scripts** in isolation:
   ```bash
   # Test that update-users generates valid YAML
   ./algo update-users --dry-run
   ```

4. **Add XML validation** for mobile configs:
   ```bash
   xmllint --noout generated_configs/*.mobileconfig
   ```

### Medium Term
1. **Mock cloud provider APIs** to test deployment logic
2. ~~**Container-based integration tests** using Docker Compose~~ ✅ DONE! See `integration/`
3. **Test certificate generation** without full deployment
4. **Validate generated configs** against schemas

### Long Term
1. **End-to-end tests** with actual VPN connections (using network namespaces)
2. **Performance testing** for large user counts
3. **Upgrade path testing** (old configs → new configs)
4. **Multi-platform client testing**

## Security Improvements (from zizmor)

Current status: ✅ No security issues found

Recommendations:
1. Add explicit job names for better workflow clarity
2. Consider pinning Ubuntu runner versions to specific releases
3. Add GITHUB_TOKEN with minimal permissions when needed for API checks

## Test Philosophy

Our approach focuses on:
1. **Fast feedback** - Tests run in < 3 minutes
2. **No flaky tests** - Avoid complex networking setups
3. **Test what matters** - Config generation, not VPN protocols
4. **Progressive enhancement** - Start simple, add coverage gradually

## Running Tests

### Unit Tests
```bash
# Run all unit tests
python -m pytest tests/unit/ -v

# Run specific test file
python tests/unit/test_basic_sanity.py

# Run with coverage
python -m pytest tests/unit/ --cov=algo
```

### Integration Tests
```bash
# Using make (recommended)
cd tests/integration
make test              # Run all tests
make test-one TEST=test_wireguard  # Run specific test
make shell-server     # Debug server container

# Using shell script
cd tests/integration
./run-docker-tests.sh

# Direct Python execution
cd tests/integration
python3 test_docker_vpn.py -v
```

### CI/CD Tests
The test suite runs automatically on:
- Every pull request
- Weekly schedule (Mondays)
- Manual workflow dispatch

View test results in GitHub Actions tab.