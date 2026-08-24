#!/usr/bin/env bash
set -euo pipefail

readonly PIP_AUDIT_VERSION="2.10.1"
readonly RETAINED_EXTRAS=("aws" "gcp" "hetzner" "linode" "openstack" "cloudstack")

audit_dir="$(mktemp -d)"
trap 'rm -rf "$audit_dir"' EXIT

audit_requirements() {
  local scope="$1"
  local requirements_file="$2"

  printf 'Auditing %s dependencies\n' "$scope"
  uvx --from "pip-audit==${PIP_AUDIT_VERSION}" pip-audit --strict \
    --requirement "$requirements_file" \
    --progress-spinner off
}

for extra in "${RETAINED_EXTRAS[@]}"; do
  requirements_file="${audit_dir}/${extra}.txt"
  uv export --frozen --quiet --extra "$extra" --no-dev \
    --no-emit-project --format requirements-txt \
    --output-file "$requirements_file"
  audit_requirements "$extra" "$requirements_file"
done

dev_requirements="${audit_dir}/dev.txt"
uv export --frozen --quiet --only-group dev \
  --no-emit-project --format requirements-txt \
  --output-file "$dev_requirements"
audit_requirements "development" "$dev_requirements"
