#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
readonly ROOT_DIR
readonly HARDENING_TEMPLATE="${ROOT_DIR}/roles/strongswan/templates/100-CustomLimitations.conf.j2"
readonly INSTANCE="algo-strongswan-${GITHUB_RUN_ID:-local}-$$"
readonly POOL="${INSTANCE}-pool"
readonly NETWORK="an-$$"
WORK_DIR="$(mktemp -d -t algo-strongswan-systemd.XXXXXX)"
readonly WORK_DIR
readonly STORAGE_DIR="${WORK_DIR}/storage"

pool_created=false
network_created=false
instance_created=false

cleanup() {
  local status=$?
  trap - EXIT INT TERM
  set +e
  if [[ "${instance_created}" == true ]]; then
    lxc delete --force "${INSTANCE}" >/dev/null 2>&1
  fi
  if [[ "${network_created}" == true ]]; then
    lxc network delete "${NETWORK}" >/dev/null 2>&1
  fi
  if [[ "${pool_created}" == true ]]; then
    lxc storage delete "${POOL}" >/dev/null 2>&1
  fi
  rm -rf "${WORK_DIR}"
  exit "${status}"
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

command -v lxc >/dev/null 2>&1 || {
  printf 'lxc is required for the StrongSwan systemd integration test\n' >&2
  exit 77
}
[[ -f "${HARDENING_TEMPLATE}" ]] || {
  printf 'StrongSwan hardening template not found: %s\n' "${HARDENING_TEMPLATE}" >&2
  exit 1
}

mkdir -p "${STORAGE_DIR}"
lxc storage create "${POOL}" dir source="${STORAGE_DIR}"
pool_created=true
lxc network create "${NETWORK}" ipv4.address=auto ipv6.address=none
network_created=true

lxc launch ubuntu:22.04 "${INSTANCE}" --vm --storage "${POOL}" --network "${NETWORK}"
instance_created=true

agent_ready=false
for _ in {1..60}; do
  if lxc exec "${INSTANCE}" -- /bin/true >/dev/null 2>&1; then
    agent_ready=true
    break
  fi
  sleep 2
done
if [[ "${agent_ready}" != true ]]; then
  printf 'LXD VM agent did not become ready within 120 seconds\n' >&2
  exit 1
fi

lxc exec "${INSTANCE}" -- cloud-init status --wait

lxc exec "${INSTANCE}" -- env DEBIAN_FRONTEND=noninteractive apt-get update
lxc exec "${INSTANCE}" -- env DEBIAN_FRONTEND=noninteractive apt-get install -y strongswan
lxc exec "${INSTANCE}" -- modprobe af_key
[[ "$(lxc exec "${INSTANCE}" -- stat -c '%a' /proc/net/pfkey)" == "444" ]]

cat >"${WORK_DIR}/algo-strongswan-hardening-test.service" <<'EOF'
[Unit]
Description=Algo StrongSwan systemd hardening regression probe

[Service]
Type=oneshot
ExecStart=/bin/true
EOF

lxc file push "${WORK_DIR}/algo-strongswan-hardening-test.service" \
  "${INSTANCE}/etc/systemd/system/algo-strongswan-hardening-test.service"
lxc exec "${INSTANCE}" -- mkdir -p \
  /etc/systemd/system/algo-strongswan-hardening-test.service.d \
  /etc/systemd/system/strongswan-starter.service.d
lxc file push "${HARDENING_TEMPLATE}" \
  "${INSTANCE}/etc/systemd/system/algo-strongswan-hardening-test.service.d/100-CustomLimitations.conf"
lxc file push "${HARDENING_TEMPLATE}" \
  "${INSTANCE}/etc/systemd/system/strongswan-starter.service.d/100-CustomLimitations.conf"

lxc exec "${INSTANCE}" -- systemctl daemon-reload
lxc exec "${INSTANCE}" -- systemctl start algo-strongswan-hardening-test.service
[[ "$(lxc exec "${INSTANCE}" -- systemctl show --property=Result --value algo-strongswan-hardening-test.service)" == "success" ]]

lxc exec "${INSTANCE}" -- systemctl restart strongswan-starter.service
lxc exec "${INSTANCE}" -- systemctl is-active --quiet strongswan-starter.service
lxc exec "${INSTANCE}" -- ipsec statusall

journal="$(lxc exec "${INSTANCE}" -- journalctl -b --no-pager \
  -u algo-strongswan-hardening-test.service -u strongswan-starter.service)"
if grep -Eiq '226/NAMESPACE|Failed to set up mount namespacing|Address family not supported|unsupported address family' <<<"${journal}"; then
  printf '%s\n' "${journal}" >&2
  exit 1
fi

printf 'StrongSwan systemd hardening integration test passed\n'
