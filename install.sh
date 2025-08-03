#!/usr/bin/env sh

set -ex

METHOD="${1:-${METHOD:-cloud}}"
ONDEMAND_CELLULAR="${2:-${ONDEMAND_CELLULAR:-false}}"
ONDEMAND_WIFI="${3:-${ONDEMAND_WIFI:-false}}"
ONDEMAND_WIFI_EXCLUDE="${4:-${ONDEMAND_WIFI_EXCLUDE:-_null}}"
STORE_PKI="${5:-${STORE_PKI:-false}}"
DNS_ADBLOCKING="${6:-${DNS_ADBLOCKING:-false}}"
SSH_TUNNELING="${7:-${SSH_TUNNELING:-false}}"
ENDPOINT="${8:-${ENDPOINT:-localhost}}"
USERS="${9:-${USERS:-user1}}"
REPO_SLUG="${10:-${REPO_SLUG:-trailofbits/algo}}"
REPO_BRANCH="${11:-${REPO_BRANCH:-master}}"
EXTRA_VARS="${12:-${EXTRA_VARS:-placeholder=null}}"
ANSIBLE_EXTRA_ARGS="${13:-${ANSIBLE_EXTRA_ARGS}}"

cd /opt/

installRequirements() {
  export DEBIAN_FRONTEND=noninteractive
  apt-get update
  apt-get install \
    python3-virtualenv \
    jq -y
}

getAlgo() {
  [ ! -d "algo" ] && git clone "https://github.com/${REPO_SLUG}" -b "${REPO_BRANCH}" algo
  cd algo

  python3 -m virtualenv --python="$(command -v python3)" .env
  # shellcheck source=/dev/null
  . .env/bin/activate
  python3 -m pip install -U pip virtualenv
  python3 -m pip install -r requirements.txt
}

publicIpFromInterface() {
  echo "Couldn't find a valid ipv4 address, using the first IP found on the interfaces as the endpoint."
  DEFAULT_INTERFACE="$(ip -4 route list match default | grep -Eo "dev .*" | awk '{print $2}')"
  ENDPOINT=$(ip -4 addr sh dev "$DEFAULT_INTERFACE" | grep -w inet | head -n1 | awk '{print $2}' | grep -oE '\b([0-9]{1,3}\.){3}[0-9]{1,3}\b')
  export ENDPOINT="${ENDPOINT}"
  echo "Using ${ENDPOINT} as the endpoint"
}

tryGetMetadata() {
  # Helper function to fetch metadata with retry
  url="$1"
  headers="$2"
  response=""
  
  # Try up to 2 times
  for attempt in 1 2; do
    if [ -n "$headers" ]; then
      response="$(curl -s --connect-timeout 5 --max-time "${METADATA_TIMEOUT}" -H "$headers" "$url" || true)"
    else
      response="$(curl -s --connect-timeout 5 --max-time "${METADATA_TIMEOUT}" "$url" || true)"
    fi
    
    # If we got a response, return it
    if [ -n "$response" ]; then
      echo "$response"
      return 0
    fi
    
    # Wait before retry (only on first attempt)
    [ $attempt -eq 1 ] && sleep 2
  done
  
  # Return empty string if all attempts failed
  echo ""
  return 1
}

publicIpFromMetadata() {
  # Set default timeout from environment or use 20 seconds
  METADATA_TIMEOUT="${METADATA_TIMEOUT:-20}"
  
  if tryGetMetadata "http://169.254.169.254/metadata/v1/vendor-data" "" | grep DigitalOcean >/dev/null; then
    ENDPOINT="$(tryGetMetadata "http://169.254.169.254/metadata/v1/interfaces/public/0/ipv4/address" "")"
  elif test "$(tryGetMetadata "http://169.254.169.254/latest/meta-data/services/domain" "")" = "amazonaws.com"; then
    ENDPOINT="$(tryGetMetadata "http://169.254.169.254/latest/meta-data/public-ipv4" "")"
  elif host -t A -W 10 metadata.google.internal 127.0.0.53 >/dev/null; then
    ENDPOINT="$(tryGetMetadata "http://metadata.google.internal/computeMetadata/v1/instance/network-interfaces/0/access-configs/0/external-ip" "Metadata-Flavor: Google")"
  elif test "$(tryGetMetadata "http://169.254.169.254/metadata/instance/compute/publisher/?api-version=2017-04-02&format=text" "Metadata:true")" = "Canonical"; then
    ENDPOINT="$(tryGetMetadata "http://169.254.169.254/metadata/instance/network/interface/0/ipv4/ipAddress/0/publicIpAddress?api-version=2017-04-02&format=text" "Metadata:true")"
  fi

  if echo "${ENDPOINT}" | grep -oE "\b([0-9]{1,3}\.){3}[0-9]{1,3}\b"; then
    export ENDPOINT="${ENDPOINT}"
    echo "Using ${ENDPOINT} as the endpoint"
  else
    publicIpFromInterface
  fi
}

deployAlgo() {
  getAlgo

  cd /opt/algo
  # shellcheck source=/dev/null
  . .env/bin/activate

  export HOME=/root
  export ANSIBLE_LOCAL_TEMP=/root/.ansible/tmp
  export ANSIBLE_REMOTE_TEMP=/root/.ansible/tmp

  # shellcheck disable=SC2086
  ansible-playbook main.yml \
    -e provider=local \
    -e "ondemand_cellular=${ONDEMAND_CELLULAR}" \
    -e "ondemand_wifi=${ONDEMAND_WIFI}" \
    -e "ondemand_wifi_exclude=${ONDEMAND_WIFI_EXCLUDE}" \
    -e "store_pki=${STORE_PKI}" \
    -e "dns_adblocking=${DNS_ADBLOCKING}" \
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
