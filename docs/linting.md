# Linting and Code Quality

This document describes the linting and code quality checks used in the Algo VPN project.

## Overview

The project uses multiple linters to ensure code quality across different file types:
- **Ansible** playbooks and roles
- **Python** library modules and tests
- **Shell** scripts
- **YAML** configuration files

## Linters in Use

### 1. Ansible Linting
- **Tool**: `ansible-lint`
- **Config**: `.ansible-lint`
- **Checks**: Best practices, security issues, deprecated syntax
- **Key Rules**:
  - `no-log-password`: Ensure passwords aren't logged
  - `no-same-owner`: File ownership should be explicit
  - `partial-become`: Avoid unnecessary privilege escalation

### 2. Python Linting
- **Tools**: 
  - `ruff` - Fast Python linter (replaces flake8, isort, etc.)
  - `black` - Code formatter
  - `mypy` - Type checker
  - `bandit` - Security linter
- **Config**: `pyproject.toml`
- **Style**: 120 character line length, Python 3.10+

### 3. Shell Script Linting
- **Tool**: `shellcheck`
- **Checks**: All `.sh` files in the repository
- **Catches**: Common shell scripting errors and pitfalls

### 4. YAML Linting
- **Tool**: `yamllint`
- **Config**: `.yamllint`
- **Rules**: Extended from default with custom line length

### 5. Security Scanning
- **Tools**:
  - `bandit` - Python security issues
  - `safety` - Known vulnerabilities in dependencies
  - `zizmor` - GitHub Actions security (run separately)

## CI/CD Integration

### Main Workflow (`main.yml`)
- **syntax-check**: Validates Ansible playbook syntax
- **basic-tests**: Runs unit tests including validation tests

### Lint Workflow (`lint.yml`)
Separate workflow with parallel jobs:
- **ansible-lint**: Ansible best practices
- **yaml-lint**: YAML formatting
- **python-lint**: Python code quality
- **shellcheck**: Shell script validation
- **security-checks**: Security scanning

## Running Linters Locally

```bash
# Ansible
ansible-lint -v *.yml roles/{local,cloud-*}/*/*.yml

# Python
ruff check .
black --check .
mypy library/

# Shell
find . -name "*.sh" -exec shellcheck {} \;

# YAML
yamllint .

# Security
bandit -r library/
safety check
```

## Current Status

Most linters are configured to warn rather than fail (`|| true`) to allow gradual adoption. As code quality improves, these should be changed to hard failures.

### Known Issues to Address:
1. Python library modules need formatting updates
2. Some Ansible tasks missing `changed_when` conditions
3. YAML files have inconsistent indentation
4. Shell scripts could use more error handling

## Contributing

When adding new code:
1. Run relevant linters before committing
2. Fix any errors (not just warnings)
3. Add linting exceptions only with good justification
4. Update linter configs if adding new file types