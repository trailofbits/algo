#!/bin/bash
set -euo pipefail

# Run the same linting as CI
echo "Running ansible-lint..."
ansible-lint .

echo "Running playbook dry-run check..."
# Test main playbook logic without making changes - catches runtime issues
ansible-playbook main.yml --check --connection=local \
  -e "server_ip=test" \
  -e "server_name=ci-test" \
  -e "IP_subject_alt_name=192.168.1.1" \
  || echo "Dry-run completed with issues - check output above"

echo "Running yamllint..."
yamllint -c .yamllint .

echo "Running ruff..."
ruff check . || true  # Start with warnings only

echo "Running shellcheck..."
find . -type f -name "*.sh" -not -path "./.git/*" -exec shellcheck {} \;

echo "All linting completed!"