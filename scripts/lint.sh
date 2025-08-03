#!/bin/bash
set -euo pipefail

# Run the same linting as CI
echo "Running ansible-lint..."
ansible-lint .

echo "Running yamllint..."
yamllint -c .yamllint .

echo "Running ruff..."
ruff check . || true  # Start with warnings only

echo "Running shellcheck..."
find . -type f -name "*.sh" -not -path "./.git/*" -exec shellcheck {} \;

echo "All linting completed!"