#!/bin/bash
set -euo pipefail
IFS=$'\n\t'

# =============================================================================
# Algo VPN End-to-End Connectivity Tests
#
# Uses Linux network namespaces to simulate a VPN client connecting to the
# server deployed on localhost. Tests both WireGuard and IPsec connectivity.
#
# Usage: sudo ./test-vpn-connectivity.sh [wireguard|ipsec|both]
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ALGO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

# Configuration
NAMESPACE="algo-client"
VETH_SERVER="veth-algo-srv"
VETH_CLIENT="veth-algo-cli"
SERVER_BRIDGE_IP="10.99.0.1"
CLIENT_BRIDGE_IP="10.99.0.2"
CONFIG_DIR="${ALGO_ROOT}/configs/localhost"
TEST_USER="${TEST_USER:-alice}"
VPN_TYPE="${1:-both}"
IPSEC_CLIENT_DIR=""
IPSEC_CLIENT_PID=""
IPSEC_VICI_URI=""
PUBLIC_IP_URL="${PUBLIC_IP_URL:-https://api.ipify.org}"
ORIGINAL_IP_FORWARD=""
ORIGINAL_RP_FILTER_ALL=""
ORIGINAL_RP_FILTER_VETH=""
NAT_RULE_ADDED=false
WG_RULE_ADDED=false
IKE_RULE_ADDED=false
NATT_RULE_ADDED=false

# WireGuard network from config.cfg defaults
WG_SERVER_IP="10.49.0.1"
DNS_SERVICE_IP="172.16.0.1"

# Colors for output (disabled if not a terminal)
if [[ -t 1 ]]; then
    RED='\033[0;31m'
    GREEN='\033[0;32m'
    YELLOW='\033[1;33m'
    NC='\033[0m'
else
    RED='' GREEN='' YELLOW='' NC=''
fi

log_info()  { echo -e "${GREEN}[INFO]${NC} $*"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC} $*"; }
log_error() { echo -e "${RED}[ERROR]${NC} $*"; }
log_step()  { echo -e "\n${GREEN}==>${NC} $*"; }

# =============================================================================
# Cleanup Functions
# =============================================================================

# shellcheck disable=SC2317,SC2329  # Function is invoked indirectly via trap
cleanup() {
    local exit_code=$?
    trap - EXIT INT TERM
    set +e
    log_step "Cleaning up test environment..."

    # Tear down WireGuard in namespace (if running)
    ip netns exec "${NAMESPACE}" wg-quick down /tmp/algo-test-wg.conf 2>/dev/null || true

    # Tear down the isolated swanctl/charon client without exposing credentials.
    if [[ -n "${IPSEC_VICI_URI}" ]]; then
        ip netns exec "${NAMESPACE}" swanctl --terminate --ike algovpn \
            --uri "${IPSEC_VICI_URI}" >/dev/null 2>&1 || true
    fi
    if [[ -n "${IPSEC_CLIENT_PID}" ]]; then
        kill "${IPSEC_CLIENT_PID}" 2>/dev/null || true
        wait "${IPSEC_CLIENT_PID}" 2>/dev/null || true
        IPSEC_CLIENT_PID=""
    fi

    # Remove exactly the firewall rules this process successfully added.
    if [[ "${NAT_RULE_ADDED}" == true ]]; then
        iptables -t nat -D POSTROUTING -s "${CLIENT_BRIDGE_IP}/32" ! -d 10.99.0.0/24 -j MASQUERADE || exit_code=1
    fi
    if [[ "${WG_RULE_ADDED}" == true ]]; then
        iptables -D INPUT -i "${VETH_SERVER}" -p udp --dport 51820 -j ACCEPT || exit_code=1
    fi
    if [[ "${IKE_RULE_ADDED}" == true ]]; then
        iptables -D INPUT -i "${VETH_SERVER}" -p udp --dport 500 -j ACCEPT || exit_code=1
    fi
    if [[ "${NATT_RULE_ADDED}" == true ]]; then
        iptables -D INPUT -i "${VETH_SERVER}" -p udp --dport 4500 -j ACCEPT || exit_code=1
    fi

    # Restore host kernel policy before removing the test interface.
    if [[ -n "${ORIGINAL_RP_FILTER_VETH}" ]]; then
        sysctl -w net.ipv4.conf."${VETH_SERVER}".rp_filter="${ORIGINAL_RP_FILTER_VETH}" >/dev/null || exit_code=1
    fi
    if [[ -n "${ORIGINAL_RP_FILTER_ALL}" ]]; then
        sysctl -w net.ipv4.conf.all.rp_filter="${ORIGINAL_RP_FILTER_ALL}" >/dev/null || exit_code=1
    fi
    if [[ -n "${ORIGINAL_IP_FORWARD}" ]]; then
        sysctl -w net.ipv4.ip_forward="${ORIGINAL_IP_FORWARD}" >/dev/null || exit_code=1
    fi

    # Delete namespace (also removes veth pair)
    ip netns del "${NAMESPACE}" 2>/dev/null || true

    # Clean up server-side veth if orphaned
    ip link del "${VETH_SERVER}" 2>/dev/null || true

    # Clean up temp files and the credential-bearing client directory.
    rm -f /tmp/algo-test-wg.conf /tmp/algo-tcpdump.log 2>/dev/null || true
    if [[ -n "${IPSEC_CLIENT_DIR}" ]]; then
        rm -rf "${IPSEC_CLIENT_DIR}"
        IPSEC_CLIENT_DIR=""
    fi
    pkill -f "tcpdump.*port 51820" 2>/dev/null || true

    log_info "Cleanup complete"
    exit "${exit_code}"
}

trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

# =============================================================================
# Namespace Setup
# =============================================================================

setup_namespace() {
    log_step "Setting up network namespace..."

    # Clean up any existing namespace first
    if ip netns list | grep -q "^${NAMESPACE}"; then
        log_warn "Namespace ${NAMESPACE} already exists, cleaning up first..."
        ip netns del "${NAMESPACE}" 2>/dev/null || true
        ip link del "${VETH_SERVER}" 2>/dev/null || true
    fi

    # Create namespace
    ip netns add "${NAMESPACE}"

    # Create veth pair
    ip link add "${VETH_SERVER}" type veth peer name "${VETH_CLIENT}"

    # Move client end to namespace
    ip link set "${VETH_CLIENT}" netns "${NAMESPACE}"

    # Configure server side
    ip addr add "${SERVER_BRIDGE_IP}/24" dev "${VETH_SERVER}"
    ip link set "${VETH_SERVER}" up

    # Preserve host policy before this privileged test changes it.
    ORIGINAL_IP_FORWARD=$(sysctl -n net.ipv4.ip_forward)
    ORIGINAL_RP_FILTER_ALL=$(sysctl -n net.ipv4.conf.all.rp_filter)
    ORIGINAL_RP_FILTER_VETH=$(sysctl -n net.ipv4.conf."${VETH_SERVER}".rp_filter)

    # Configure client side (in namespace)
    ip netns exec "${NAMESPACE}" ip addr add "${CLIENT_BRIDGE_IP}/24" dev "${VETH_CLIENT}"
    ip netns exec "${NAMESPACE}" ip link set "${VETH_CLIENT}" up
    ip netns exec "${NAMESPACE}" ip link set lo up

    # Set default route in namespace to go through the veth to server
    ip netns exec "${NAMESPACE}" ip route add default via "${SERVER_BRIDGE_IP}"

    # Enable forwarding on the server for NAT
    sysctl -w net.ipv4.ip_forward=1 > /dev/null

    # Add MASQUERADE for the client namespace traffic going to external networks
    iptables -t nat -A POSTROUTING -s "${CLIENT_BRIDGE_IP}/32" ! -d 10.99.0.0/24 -j MASQUERADE
    NAT_RULE_ADDED=true

    # Allow WireGuard and IPsec traffic on the veth interface
    # Use -I to insert at beginning of chain (before any DROP rules)
    iptables -I INPUT -i "${VETH_SERVER}" -p udp --dport 51820 -j ACCEPT
    WG_RULE_ADDED=true
    iptables -I INPUT -i "${VETH_SERVER}" -p udp --dport 500 -j ACCEPT
    IKE_RULE_ADDED=true
    iptables -I INPUT -i "${VETH_SERVER}" -p udp --dport 4500 -j ACCEPT
    NATT_RULE_ADDED=true

    log_info "Namespace ${NAMESPACE} created with IP ${CLIENT_BRIDGE_IP}"

    # Verify connectivity to server
    if ip netns exec "${NAMESPACE}" ping -c 1 -W 2 "${SERVER_BRIDGE_IP}" > /dev/null 2>&1; then
        log_info "Namespace can reach server bridge at ${SERVER_BRIDGE_IP}"
    else
        log_error "Namespace cannot reach server bridge. Network setup failed."
        log_error "Fix: Check veth configuration and firewall rules"
        exit 1
    fi

    # Verify client can reach WireGuard port on localhost (through NAT)
    if ip netns exec "${NAMESPACE}" timeout 2 bash -c "echo >/dev/udp/127.0.0.1/51820" 2>/dev/null; then
        log_info "Client can reach WireGuard port (UDP 51820)"
    else
        log_warn "Cannot verify WireGuard port reachability (may be expected)"
    fi
}

# =============================================================================
# Mobileconfig Validation
# =============================================================================

test_mobileconfig_validation() {
    log_step "Validating mobileconfig files..."

    local failed=0

    # WireGuard mobileconfig (if exists)
    if [[ -d "${CONFIG_DIR}/wireguard/apple" ]]; then
        while IFS= read -r -d '' f; do
            if xmllint --noout "${f}" 2>/dev/null; then
                log_info "Valid XML: $(basename "${f}")"
            else
                log_error "Invalid XML: ${f}"
                ((failed++))
            fi
        done < <(find "${CONFIG_DIR}/wireguard/apple" -name "*.mobileconfig" -print0 2>/dev/null)
    fi

    # IPsec mobileconfig
    if [[ -d "${CONFIG_DIR}/ipsec/apple" ]]; then
        while IFS= read -r -d '' f; do
            if xmllint --noout "${f}" 2>/dev/null; then
                log_info "Valid XML: $(basename "${f}")"
            else
                log_error "Invalid XML: ${f}"
                ((failed++))
            fi
        done < <(find "${CONFIG_DIR}/ipsec/apple" -name "*.mobileconfig" -print0 2>/dev/null)
    fi

    if [[ ${failed} -eq 0 ]]; then
        log_info "All mobileconfig files valid"
        return 0
    else
        log_error "${failed} mobileconfig file(s) invalid"
        return 1
    fi
}

# =============================================================================
# CA Name Constraints Test
# =============================================================================

test_ca_name_constraints() {
    log_step "Testing CA name constraints..."

    local cacert="${CONFIG_DIR}/ipsec/.pki/cacert.pem"
    local server_cert
    server_cert=$(find "${CONFIG_DIR}/ipsec/.pki/certs" -name "*.crt" ! -name "${TEST_USER}.crt" | head -1)

    if [[ ! -f "${cacert}" ]]; then
        log_warn "Skipping CA name constraints test (CA cert not found)"
        return 0
    fi

    if [[ -z "${server_cert}" ]] || [[ ! -f "${server_cert}" ]]; then
        log_warn "Skipping CA name constraints test (server cert not found)"
        return 0
    fi

    # The CA should verify the server certificate
    local verify_output
    verify_output=$(openssl verify -verbose -CAfile "${cacert}" "${server_cert}" 2>&1) || true

    if echo "${verify_output}" | grep -q "OK"; then
        log_info "Server certificate verification passed"
    else
        log_warn "Server certificate verification: ${verify_output}"
    fi

    log_info "CA name constraints test completed"
    return 0
}

# =============================================================================
# WireGuard Tests
# =============================================================================

test_wireguard() {
    log_step "Testing WireGuard connectivity..."

    local wg_config="${CONFIG_DIR}/wireguard/${TEST_USER}.conf"

    if [[ ! -f "${wg_config}" ]]; then
        log_error "WireGuard config not found: ${wg_config}"
        log_error "Fix: Ensure Algo deployed with wireguard_enabled: true"
        return 1
    fi

    # Copy and modify config for namespace use
    local ns_config="/tmp/algo-test-wg.conf"
    cp "${wg_config}" "${ns_config}"

    # Modify config:
    # - Change Endpoint to use bridge IP (client namespace routes through veth)
    # - Set Table=off to prevent routing table changes conflicting with namespace
    # - Remove DNS line to avoid resolvconf dependency (we test DNS separately)
    sed -i "s/Endpoint = 127.0.0.1:/Endpoint = ${SERVER_BRIDGE_IP}:/" "${ns_config}"
    sed -i "s/Endpoint = localhost:/Endpoint = ${SERVER_BRIDGE_IP}:/" "${ns_config}"
    sed -i '/^DNS = /d' "${ns_config}"

    # Add Table=off if not present (prevent routing table changes in namespace)
    if ! grep -q "^Table" "${ns_config}"; then
        sed -i '/^\[Interface\]/a Table = off' "${ns_config}"
    fi

    # Add PersistentKeepalive to trigger handshake initiation
    # Without this, WireGuard waits for outgoing traffic before initiating
    if ! grep -q "^PersistentKeepalive" "${ns_config}"; then
        sed -i '/^\[Peer\]/a PersistentKeepalive = 1' "${ns_config}"
    fi

    log_info "Modified WireGuard config for namespace testing"
    log_info "Endpoint changed to ${SERVER_BRIDGE_IP}"

    # Debug: Show server WireGuard state before client connects
    log_info "Server WireGuard peers:"
    local server_peers
    server_peers=$(wg show wg0 peers 2>/dev/null || echo "")
    if [[ -n "${server_peers}" ]]; then
        log_info "Found peers: ${server_peers}"
    else
        log_error "Server WireGuard has no peers configured!"
        log_error "Check that deployment created /etc/wireguard/wg0.conf with [Peer] sections"
        return 1
    fi
    log_info "Server WireGuard listening:"
    ss -ulnp | grep 51820 || log_warn "WireGuard port not found in ss output"

    # Disable reverse path filtering on veth (can cause packet drops in some environments)
    sysctl -w net.ipv4.conf.all.rp_filter=0 > /dev/null 2>&1 || true
    sysctl -w net.ipv4.conf."${VETH_SERVER}".rp_filter=0 > /dev/null 2>&1 || true

    # Start packet capture in background for failure diagnosis
    local tcpdump_log="/tmp/algo-tcpdump.log"
    timeout 20 tcpdump -i any -n port 51820 -c 20 > "${tcpdump_log}" 2>&1 &
    local tcpdump_pid=$!

    # Start WireGuard in the namespace
    log_info "Starting WireGuard in namespace..."
    if ! ip netns exec "${NAMESPACE}" wg-quick up "${ns_config}" 2>&1; then
        log_error "Failed to start WireGuard in namespace"
        kill "${tcpdump_pid}" 2>/dev/null || true
        return 1
    fi

    # Get the WireGuard interface name
    local wg_interface
    wg_interface=$(ip netns exec "${NAMESPACE}" wg show interfaces 2>/dev/null || echo "")

    if [[ -z "${wg_interface}" ]]; then
        log_error "WireGuard interface not created in namespace"
        return 1
    fi
    log_info "WireGuard interface '${wg_interface}' is up"

    # Add routes for VPN traffic through wg interface
    ip netns exec "${NAMESPACE}" ip route add "${WG_SERVER_IP}/32" dev "${wg_interface}" 2>/dev/null || true
    ip netns exec "${NAMESPACE}" ip route add "${DNS_SERVICE_IP}/32" dev "${wg_interface}" 2>/dev/null || true

    # Wait for handshake (with timeout)
    log_info "Waiting for WireGuard handshake..."
    local attempts=0
    local max_attempts=15
    while [[ ${attempts} -lt ${max_attempts} ]]; do
        if ip netns exec "${NAMESPACE}" wg show 2>/dev/null | grep -q "latest handshake"; then
            log_info "WireGuard handshake completed!"
            break
        fi
        sleep 1
        ((attempts++))
    done

    if [[ ${attempts} -ge ${max_attempts} ]]; then
        log_error "WireGuard handshake timeout after ${max_attempts} seconds"
        log_error "Debug - client wg show:"
        ip netns exec "${NAMESPACE}" wg show 2>&1 || true
        log_error "Debug - server wg0 state:"
        wg show wg0 2>&1 || true
        log_error "Debug - iptables INPUT chain (first 15 rules):"
        iptables -L INPUT -n -v --line-numbers 2>&1 | head -20 || true
        log_error "Debug - packet capture (tcpdump):"
        kill "${tcpdump_pid}" 2>/dev/null || true
        sleep 1
        cat "${tcpdump_log}" 2>/dev/null || echo "No capture available"
        log_error "Debug - host route to 10.99.0.0/24:"
        ip route get 10.99.0.2 2>&1 || true
        log_error "Debug - namespace route to server:"
        ip netns exec "${NAMESPACE}" ip route get 10.99.0.1 2>&1 || true
        return 1
    fi

    # Stop packet capture
    kill "${tcpdump_pid}" 2>/dev/null || true

    # Show WireGuard status
    ip netns exec "${NAMESPACE}" wg show

    # Test connectivity to VPN server IP
    log_info "Testing ping to WireGuard server (${WG_SERVER_IP})..."
    if ip netns exec "${NAMESPACE}" ping -c 3 -W 3 "${WG_SERVER_IP}" 2>&1; then
        log_info "Ping to WireGuard server successful"
    else
        log_error "Cannot ping WireGuard server IP ${WG_SERVER_IP}"
        return 1
    fi

    # Test DNS through VPN (hard fail as per user decision)
    log_info "Testing DNS resolution through VPN (${DNS_SERVICE_IP})..."
    if ip netns exec "${NAMESPACE}" host -W 5 google.com "${DNS_SERVICE_IP}" 2>&1; then
        log_info "DNS resolution through VPN successful"
    else
        log_error "DNS resolution through VPN failed"
        log_error "Fix: Check dnscrypt-proxy service and routing to ${DNS_SERVICE_IP}"
        return 1
    fi

    # Cleanup WireGuard
    ip netns exec "${NAMESPACE}" wg-quick down "${ns_config}" 2>/dev/null || true
    rm -f "${ns_config}"

    log_info "WireGuard E2E tests PASSED"
    return 0
}

# =============================================================================
# IPsec Tests
# =============================================================================

test_ipsec() {
    log_step "Testing a genuine IPsec/StrongSwan tunnel..."

    local cacert="${CONFIG_DIR}/ipsec/.pki/cacert.pem"
    local user_cert="${CONFIG_DIR}/ipsec/.pki/certs/${TEST_USER}.crt"
    local user_key="${CONFIG_DIR}/ipsec/.pki/private/${TEST_USER}.key"
    local server_id="127.0.0.1"
    local charon_binary=""
    local candidate_owner candidate_mode
    local client_config vici_socket sa_status
    local server_source_ip vpn_source_ip

    for f in "${cacert}" "${user_cert}" "${user_key}"; do
        if [[ ! -f "${f}" ]]; then
            log_error "Required generated IPsec credential is missing"
            log_error "Fix: deploy localhost with IPsec and store_pki enabled"
            return 1
        fi
    done

    if ! openssl verify -CAfile "${cacert}" "${user_cert}" >/dev/null 2>&1; then
        log_error "Generated client certificate does not verify against the generated CA"
        return 1
    fi

    # Never make copied credentials group/world-readable or echo their contents.
    umask 077
    IPSEC_CLIENT_DIR=$(mktemp -d /tmp/algo-ipsec-client.XXXXXX) || return 1
    chmod 700 "${IPSEC_CLIENT_DIR}" || return 1
    client_config="${IPSEC_CLIENT_DIR}/swanctl.conf"
    vici_socket="${IPSEC_CLIENT_DIR}/charon.vici"
    IPSEC_VICI_URI="unix://${vici_socket}"

    install -m 600 "${cacert}" "${IPSEC_CLIENT_DIR}/cacert.pem" || return 1
    install -m 600 "${user_cert}" "${IPSEC_CLIENT_DIR}/client.crt" || return 1
    install -m 600 "${user_key}" "${IPSEC_CLIENT_DIR}/client.key" || return 1

    if ! cat > "${client_config}" <<EOF
connections {
    algovpn {
        version = 2
        proposals = aes256gcm16-prfsha512-ecp384
        rekey_time = 0
        dpd_delay = 35s
        remote_addrs = ${SERVER_BRIDGE_IP}
        vips = 0.0.0.0
        local {
            auth = pubkey
            certs = ${IPSEC_CLIENT_DIR}/client.crt
        }
        remote {
            auth = pubkey
            id = ${server_id}
        }
        children {
            algovpn {
                esp_proposals = aes256gcm16-ecp384
                local_ts = dynamic
                remote_ts = 0.0.0.0/0
                rekey_time = 0
                dpd_action = clear
            }
        }
    }
}
authorities {
    algo {
        cacert = ${IPSEC_CLIENT_DIR}/cacert.pem
    }
}
secrets {
    private-client {
        file = ${IPSEC_CLIENT_DIR}/client.key
    }
}
EOF
    then
        return 1
    fi
    chmod 600 "${client_config}" || return 1

    if ! cat > "${IPSEC_CLIENT_DIR}/strongswan.conf" <<EOF
charon {
    load_modular = yes
    install_routes = yes
    install_virtual_ip = yes
    plugins {
        include /etc/strongswan.d/charon/*.conf
        vici {
            socket = "unix://${vici_socket}"
        }
    }
    filelog {
        stderr {
            default = 1
            ike = 1
            append = no
            flush_line = yes
        }
    }
}
EOF
    then
        return 1
    fi
    chmod 600 "${IPSEC_CLIENT_DIR}/strongswan.conf" || return 1

    for candidate in /usr/lib/ipsec/charon /usr/libexec/ipsec/charon; do
        if [[ ! -x "${candidate}" || ! -f "${candidate}" || -L "${candidate}" ]]; then
            continue
        fi
        candidate_owner=$(stat -c "%u" -- "${candidate}") || continue
        candidate_mode=$(stat -c "%a" -- "${candidate}") || continue
        if [[ "${candidate_owner}" != "0" ]] || (( (8#${candidate_mode} & 8#022) != 0 )); then
            continue
        fi
        charon_binary="${candidate}"
        break
    done
    if [[ -z "${charon_binary}" ]]; then
        log_error "charon executable not found; install the strongSwan charon package"
        return 1
    fi
    # Ubuntu attaches the host AppArmor profile to the packaged charon path.
    # Execute a root-owned private copy so the isolated test client can read
    # its private namespace configuration without weakening the server profile.
    install -m 0700 "${charon_binary}" "${IPSEC_CLIENT_DIR}/charon-client" || return 1
    charon_binary="${IPSEC_CLIENT_DIR}/charon-client"

    log_info "Starting an isolated charon client in namespace ${NAMESPACE}"
    ip netns exec "${NAMESPACE}" unshare --mount --pid --fork --kill-child --mount-proc \
        sh -c 'mount --make-rprivate / && mount -t tmpfs -o mode=0755,nosuid,nodev tmpfs /run && exec "$@"' \
        sh env STRONGSWAN_CONF="${IPSEC_CLIENT_DIR}/strongswan.conf" \
        "${charon_binary}" >"${IPSEC_CLIENT_DIR}/launcher.log" 2>&1 &
    IPSEC_CLIENT_PID=$!

    local attempts=0
    while [[ ! -S "${vici_socket}" && ${attempts} -lt 10 ]]; do
        if ! kill -0 "${IPSEC_CLIENT_PID}" 2>/dev/null; then
            log_error "Isolated charon client exited before opening its control socket"
            sed -E "s#${IPSEC_CLIENT_DIR}#<redacted-client-dir>#g" \
                "${IPSEC_CLIENT_DIR}/launcher.log" >&2 || true
            return 1
        fi
        sleep 1 || return 1
        ((attempts += 1))
    done
    if [[ ! -S "${vici_socket}" ]]; then
        log_error "Timed out waiting for the isolated charon control socket"
        return 1
    fi

    log_info "Loading generated credentials and connection into the isolated client"
    if ! ip netns exec "${NAMESPACE}" swanctl --load-all \
        --file "${client_config}" --uri "${IPSEC_VICI_URI}" >/dev/null; then
        log_error "swanctl failed to load the isolated client configuration"
        return 1
    fi

    log_info "Initiating IKEv2 and CHILD SA from the client namespace"
    if ! ip netns exec "${NAMESPACE}" swanctl --initiate --child algovpn \
        --timeout 30 --uri "${IPSEC_VICI_URI}" >/dev/null; then
        log_error "swanctl failed to initiate the IPsec tunnel"
        return 1
    fi

    sa_status=$(ip netns exec "${NAMESPACE}" swanctl --list-sas \
        --uri "${IPSEC_VICI_URI}" 2>&1) || return 1
    if ! grep -q "ESTABLISHED" <<<"${sa_status}"; then
        log_error "The client has no ESTABLISHED IKE SA"
        return 1
    fi
    if ! grep -q "INSTALLED" <<<"${sa_status}"; then
        log_error "The client has no INSTALLED CHILD SA"
        return 1
    fi
    log_info "IKE SA is ESTABLISHED and CHILD SA is INSTALLED"

    local xfrm_bytes_before xfrm_bytes_after
    xfrm_bytes_before=$(ip netns exec "${NAMESPACE}" ip -s xfrm state |
        awk -f "${SCRIPT_DIR}/xfrm-byte-count.awk") || return 1

    log_info "Resolving DNS explicitly through the VPN service"
    if ! ip netns exec "${NAMESPACE}" dig "@${DNS_SERVICE_IP}" google.com \
        +short +time=5 +tries=1 | grep -q .; then
        log_error "DNS resolution through the IPsec tunnel failed"
        return 1
    fi

    # Both values stay out of logs to avoid leaking runner/network metadata.
    if ! server_source_ip=$(curl --fail --silent --show-error --max-time 15 "${PUBLIC_IP_URL}"); then
        log_error "Could not obtain the server source IP from the test endpoint"
        return 1
    fi
    if ! vpn_source_ip=$(ip netns exec "${NAMESPACE}" curl --fail --silent \
        --show-error --max-time 15 "${PUBLIC_IP_URL}"); then
        log_error "Routed HTTPS fetch through the IPsec tunnel failed"
        return 1
    fi
    if [[ -z "${server_source_ip}" || "${vpn_source_ip}" != "${server_source_ip}" ]]; then
        log_error "VPN source IP does not match server source IP"
        return 1
    fi
    log_info "Routed HTTPS fetch used the VPN server source IP"

    xfrm_bytes_after=$(ip netns exec "${NAMESPACE}" ip -s xfrm state |
        awk -f "${SCRIPT_DIR}/xfrm-byte-count.awk") || return 1
    if ! ((xfrm_bytes_after > xfrm_bytes_before)); then
        log_error "IPsec XFRM byte counters did not increase during DNS and HTTPS probes"
        return 1
    fi
    log_info "IPsec XFRM counters prove the probes traversed the CHILD SA"

    ip netns exec "${NAMESPACE}" swanctl --terminate --ike algovpn \
        --uri "${IPSEC_VICI_URI}" >/dev/null || return 1
    IPSEC_VICI_URI=""
    kill "${IPSEC_CLIENT_PID}" || return 1
    wait "${IPSEC_CLIENT_PID}" 2>/dev/null || true
    IPSEC_CLIENT_PID=""
    rm -rf "${IPSEC_CLIENT_DIR}" || return 1
    IPSEC_CLIENT_DIR=""

    log_info "IPsec genuine tunnel E2E tests PASSED"
}

# =============================================================================
# Debug Information Collection
# =============================================================================

collect_debug_info() {
    log_step "Collecting debug information..."

    echo "=== Network Interfaces (Host) ==="
    ip addr || true

    echo "=== Routing Table (Host) ==="
    ip route || true

    echo "=== Network Namespaces ==="
    ip netns list || true

    echo "=== Network Interfaces (Namespace) ==="
    ip netns exec "${NAMESPACE}" ip addr 2>/dev/null || echo "Namespace not available"

    echo "=== Routing Table (Namespace) ==="
    ip netns exec "${NAMESPACE}" ip route 2>/dev/null || echo "Namespace not available"

    echo "=== WireGuard Status (Host) ==="
    wg show || true

    echo "=== WireGuard Status (Namespace) ==="
    ip netns exec "${NAMESPACE}" wg show 2>/dev/null || echo "Not running"

    echo "=== IPsec Status (Host) ==="
    ipsec statusall || true

    echo "=== Listening Ports ==="
    ss -tulnp | grep -E ':(51820|500|4500|53)\s' || true

    echo "=== iptables NAT rules ==="
    iptables -t nat -L POSTROUTING -n -v || true

    echo "=== DNS Service Status ==="
    systemctl status dnscrypt-proxy --no-pager 2>/dev/null || true

    echo "=== Recent System Logs ==="
    journalctl -n 50 --no-pager 2>/dev/null || true
}

# =============================================================================
# Main
# =============================================================================

main() {
    log_step "Algo VPN End-to-End Connectivity Tests"
    log_info "VPN type: ${VPN_TYPE}"
    log_info "Config directory: ${CONFIG_DIR}"
    log_info "Test user: ${TEST_USER}"

    # Check root
    if [[ ${EUID} -ne 0 ]]; then
        log_error "This script must be run as root (for namespace operations)"
        log_error "Fix: sudo $0 ${VPN_TYPE}"
        exit 1
    fi

    # Check required commands
    local missing_cmds=()
    for cmd in ip wg wg-quick swanctl xmllint openssl host dig curl unshare mount; do
        if ! command -v "${cmd}" &> /dev/null; then
            missing_cmds+=("${cmd}")
        fi
    done

    if [[ ${#missing_cmds[@]} -gt 0 ]]; then
        log_error "Required command(s) not found: ${missing_cmds[*]}"
        log_error "Fix: apt-get install iproute2 wireguard-tools strongswan strongswan-swanctl libxml2-utils openssl dnsutils curl"
        exit 1
    fi

    # Check config directory exists
    if [[ ! -d "${CONFIG_DIR}" ]]; then
        log_error "Config directory not found: ${CONFIG_DIR}"
        log_error "Fix: Deploy Algo first: ansible-playbook main.yml -e provider=local"
        exit 1
    fi

    local exit_code=0

    # Run validation tests first (no namespace needed)
    if ! test_mobileconfig_validation; then
        exit_code=$((exit_code + 1))
    fi
    if ! test_ca_name_constraints; then
        exit_code=$((exit_code + 1))
    fi

    # Setup namespace for connectivity tests
    setup_namespace

    # Run protocol-specific tests
    case "${VPN_TYPE}" in
        wireguard)
            if ! test_wireguard; then
                exit_code=$((exit_code + 1))
            fi
            ;;
        ipsec)
            if ! test_ipsec; then
                exit_code=$((exit_code + 1))
            fi
            ;;
        both)
            if ! test_wireguard; then
                exit_code=$((exit_code + 1))
            fi
            if ! test_ipsec; then
                exit_code=$((exit_code + 1))
            fi
            ;;
        *)
            log_error "Unknown VPN type: ${VPN_TYPE}"
            log_error "Usage: $0 [wireguard|ipsec|both]"
            exit 1
            ;;
    esac

    # Summary
    log_step "Test Summary"
    if [[ ${exit_code} -eq 0 ]]; then
        log_info "All E2E tests PASSED"
    else
        log_error "${exit_code} test(s) FAILED"
        collect_debug_info
    fi

    exit ${exit_code}
}

main "$@"
