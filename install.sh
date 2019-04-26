#!/usr/bin/env sh

set -ex

METHOD="${1:-${METHOD:-cloud}}"
ONDEMAND_CELLULAR="${2:-${ONDEMAND_CELLULAR:-false}}"
ONDEMAND_WIFI="${3:-${ONDEMAND_WIFI:-false}}"
ONDEMAND_WIFI_EXCLUDE="${4:-${ONDEMAND_WIFI_EXCLUDE:-_null}}"
WINDOWS="${5:-${WINDOWS:-false}}"
STORE_CAKEY="${6:-${STORE_CAKEY:-false}}"
LOCAL_DNS="${7:-${LOCAL_DNS:-false}}"
SSH_TUNNELING="${8:-${SSH_TUNNELING:-false}}"
ENDPOINT="${9:-${ENDPOINT:-localhost}}"
USERS="${10:-${USERS:-user1}}"
REPO_SLUG="${11:-${REPO_SLUG:-trailofbits/algo}}"
REPO_BRANCH="${12:-${REPO_BRANCH:-master}}"
EXTRA_VARS="${13:-${EXTRA_VARS:-placeholder=null}}"
ANSIBLE_EXTRA_ARGS="${14:-${ANSIBLE_EXTRA_ARGS}}"

cd /opt/

installRequirements() {
  apt-get update
  apt-get install \
    software-properties-common \
    git \
    build-essential \
    libssl-dev \
    libffi-dev \
    python-dev \
    python-pip \
    python-setuptools \
    python-virtualenv \
    bind9-host \
    jq -y
}

getAlgo() {
  [ ! -d "algo" ] && git clone "https://github.com/${REPO_SLUG}" -b "${REPO_BRANCH}" algo
  cd algo
  
  python -m virtualenv --python="$(command -v python2)" .venv
  # shellcheck source=/dev/null
  . .venv/bin/activate
  python -m pip install -U pip virtualenv
  python -m pip install -r requirements.txt
}

publicIpFromInterface() {
  echo "Couldn't find a valid ipv4 address, using the first IP found on the interfaces as the endpoint."
  DEFAULT_INTERFACE="$(ip -4 route list match default | grep -Eo "dev .*" | awk '{print $2}')"
  ENDPOINT=$(ip -4 addr sh dev "$DEFAULT_INTERFACE" | grep -w inet | head -n1 | awk '{print $2}' | grep -oE '\b([0-9]{1,3}\.){3}[0-9]{1,3}\b')
  export ENDPOINT=$ENDPOINT
  echo "Using ${ENDPOINT} as the endpoint"
}

publicIpFromMetadata() {
  if curl -s http://169.254.169.254/metadata/v1/vendor-data | grep DigitalOcean >/dev/null; then
    ENDPOINT="$(curl -s http://169.254.169.254/metadata/v1/interfaces/public/0/ipv4/address)"
  elif test "$(curl -s http://169.254.169.254/latest/meta-data/services/domain)" = "amazonaws.com"; then
    ENDPOINT="$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)"
  elif host -t A -W 10 metadata.google.internal 127.0.0.53 >/dev/null; then
    ENDPOINT="$(curl -H "Metadata-Flavor: Google" "http://metadata.google.internal/computeMetadata/v1/instance/network-interfaces/0/access-configs/0/external-ip")"
  elif test "$(curl -s -H Metadata:true 'http://169.254.169.254/metadata/instance/compute/publisher/?api-version=2017-04-02&format=text')" = "Canonical"; then
    ENDPOINT="$(curl -H Metadata:true 'http://169.254.169.254/metadata/instance/network/interface/0/ipv4/ipAddress/0/publicIpAddress?api-version=2017-04-02&format=text')"
  fi

  if echo "${ENDPOINT}" | grep -oE "\b([0-9]{1,3}\.){3}[0-9]{1,3}\b"; then
    export ENDPOINT=$ENDPOINT
    echo "Using ${ENDPOINT} as the endpoint"
  else
    publicIpFromInterface
  fi
}

deployAlgo() {
  getAlgo

  cd /opt/algo
  # shellcheck source=/dev/null
  . .venv/bin/activate

  export HOME=/root
  export ANSIBLE_LOCAL_TEMP=/root/.ansible/tmp
  export ANSIBLE_REMOTE_TEMP=/root/.ansible/tmp

  # shellcheck disable=SC2086
  ansible-playbook main.yml \
    -e provider=local \
    -e "ondemand_cellular=${ONDEMAND_CELLULAR}" \
    -e "ondemand_wifi=${ONDEMAND_WIFI}" \
    -e "ondemand_wifi_exclude=${ONDEMAND_WIFI_EXCLUDE}" \
    -e "windows=${WINDOWS}" \
    -e "store_cakey=${STORE_CAKEY}" \
    -e "local_dns=${LOCAL_DNS}" \
    -e "ssh_tunneling=${SSH_TUNNELING}" \
    -e "endpoint=$ENDPOINT" \
    -e "users=$(echo "$USERS" | jq -Rc 'split(",")')" \
    -e server=localhost \
    -e ssh_user=root \
    -e "${EXTRA_VARS}" \
    --skip-tags debug ${ANSIBLE_EXTRA_ARGS} |
      tee /var/log/algo.log
}

if test "$METHOD" = "cloud"; then
  publicIpFromMetadata
fi

installRequirements

deployAlgo
