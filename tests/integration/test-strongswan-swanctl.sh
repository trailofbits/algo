#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
readonly ROOT_DIR
readonly TEMPLATES="${ROOT_DIR}/roles/strongswan/templates"
readonly HARDENING="${TEMPLATES}/100-CustomLimitations.conf.j2"
readonly INSTANCE="algo-swanctl-${GITHUB_RUN_ID:-local}-$$"
readonly POOL="${INSTANCE}-pool"
readonly NETWORK="asw${GITHUB_RUN_ID:-$$}"
WORK_DIR="$(mktemp -d -t algo-strongswan-swanctl.XXXXXX)"
readonly WORK_DIR
readonly STORAGE_DIR="${WORK_DIR}/storage"
readonly RENDERED_DIR="${WORK_DIR}/rendered"

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
  printf 'lxc is required for the StrongSwan swanctl integration test\n' >&2
  exit 77
}
command -v uv >/dev/null 2>&1 || {
  printf 'uv is required to render the StrongSwan templates\n' >&2
  exit 77
}
[[ -f "${HARDENING}" ]] || {
  printf 'StrongSwan hardening template is missing\n' >&2
  exit 1
}

uv run --frozen python tests/integration/render-strongswan-swanctl.py \
  --templates "${TEMPLATES}" --output "${RENDERED_DIR}"
mkdir -p "${STORAGE_DIR}"
lxc storage create "${POOL}" dir source="${STORAGE_DIR}"
pool_created=true
lxc network create "${NETWORK}" ipv4.address=auto ipv6.address=none
network_created=true
lxc launch ubuntu:24.04 "${INSTANCE}" --vm --storage "${POOL}" --network "${NETWORK}"
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
  printf 'Ubuntu 24.04 LXD VM agent did not become ready within 120 seconds\n' >&2
  exit 1
fi
lxc exec "${INSTANCE}" -- cloud-init status --wait
lxc exec "${INSTANCE}" -- env DEBIAN_FRONTEND=noninteractive apt-get update
lxc exec "${INSTANCE}" -- env DEBIAN_FRONTEND=noninteractive apt-get install -y \
  charon-systemd strongswan-swanctl strongswan-pki
lxc exec "${INSTANCE}" -- systemctl stop strongswan
lxc exec "${INSTANCE}" -- install -d -m 0755 \
  /etc/swanctl/x509ca /etc/swanctl/x509 /etc/swanctl/private /etc/swanctl/x509crl \
  /etc/systemd/system/strongswan.service.d
lxc exec "${INSTANCE}" -- install -d -m 0755 /var/lib/strongswan
lxc exec "${INSTANCE}" -- id strongswan >/dev/null 2>&1 || \
  lxc exec "${INSTANCE}" -- useradd --system --home /var/lib/strongswan \
    --shell /usr/sbin/nologin --gid nogroup strongswan
lxc file push "${RENDERED_DIR}/swanctl.conf" "${INSTANCE}/etc/swanctl/swanctl.conf"
lxc file push "${RENDERED_DIR}/strongswan.conf" "${INSTANCE}/etc/strongswan.conf"
lxc file push "${HARDENING}" \
  "${INSTANCE}/etc/systemd/system/strongswan.service.d/100-CustomLimitations.conf"

lxc exec "${INSTANCE}" -- bash -c '
set -euo pipefail
pki --gen --type ecdsa --size 384 --outform pem > /etc/swanctl/private/ca.key
pki --self --ca --lifetime 3650 --in /etc/swanctl/private/ca.key --type ecdsa \
  --dn "CN=Algo Test CA" --outform pem > /etc/swanctl/x509ca/ca.crt
pki --gen --type ecdsa --size 384 --outform pem > /etc/swanctl/private/10.99.0.1.key
pki --pub --in /etc/swanctl/private/10.99.0.1.key --type ecdsa | \
  pki --issue --lifetime 365 --cacert /etc/swanctl/x509ca/ca.crt \
  --cakey /etc/swanctl/private/ca.key --dn "CN=10.99.0.1" --san 10.99.0.1 \
  --flag serverAuth --flag ikeIntermediate --outform pem \
  > /etc/swanctl/x509/10.99.0.1.crt
chown -R strongswan:nogroup /etc/swanctl/private /etc/swanctl/x509 /etc/swanctl/x509ca
chmod 0600 /etc/swanctl/swanctl.conf /etc/swanctl/private/*
systemctl daemon-reload
if ! systemctl restart strongswan; then
  systemctl status strongswan --no-pager || true
  journalctl -b --no-pager -u strongswan.service || true
  exit 1
fi
sleep 2
swanctl --load-all --noprompt
swanctl --list-conns | grep -q ikev2-pubkey
systemctl is-active --quiet strongswan
systemctl show strongswan --property=ProtectSystem --value | grep -Fx strict
'

journal="$(lxc exec "${INSTANCE}" -- journalctl -b --no-pager -u strongswan.service)"
if grep -Eiq 'failed to load connection|parsing.*failed|226/NAMESPACE|unsupported address family' <<<"${journal}"; then
  printf '%s\n' "${journal}" >&2
  exit 1
fi
printf 'Ubuntu 24.04 StrongSwan swanctl native load passed\n'
