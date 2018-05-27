#!/usr/bin/env bash

# Terminate if command or chain of command finishes with a non-zero exit status.
set -e
# Terminate if an uninitialized variable is accessed.
set -u

main() {
    local CONNECTION_NAME="$1"
    local USERNAME="$2"
    local IPADDRESS="$3"
    local USER="$4"
    delete_existing_ipsec_vpn "${CONNECTION_NAME}"
    create_nm_ipsec_vpn "${CONNECTION_NAME}" "${USERNAME}" "${IPADDRESS}" "${USER}"
}

delete_existing_ipsec_vpn() {
    local CONNECTION_NAME="$1"
    # Delete the profile if it already exists
    nmcli con delete "${CONNECTION_NAME}" || true
}

create_nm_ipsec_vpn() {
    local CONNECTION_NAME="$1"
    local USERNAME="$2"
    local IPADDRESS="$3"
    local USER="$4"
    # Create initial connection object
    nmcli connection add \
          con-name "$CONNECTION_NAME" \
          ifname \* \
          type vpn \
          autoconnect false \
          vpn-type strongswan

    # Only allow current user to use VPN
    nmcli connection modify "$CONNECTION_NAME" connection.permissions "user:${USER}"

    local VPN_OPTIONS=( \
              #####################
              "address=${IPADDRESS}" \
              "certificate=/etc/ipsec.d/cacerts/${IPADDRESS}.pem" \
              "encap=yes" \
              "esp=aes128gcm16-ecp256;aes128-sha2_512-prfsha512-ecp256" \
              "ike=aes128gcm16-prfsha512-ecp256;aes128-sha2_512-prfsha512-ecp256;aes128-sha2_384-prfsha384-ecp256" \
              "ipcomp=yes" \
              "method=key" \
              "proposal=yes" \
              "usercert=/etc/ipsec.d/certs/${USERNAME}.crt" \
              "userkey=/etc/ipsec.d/private/${USERNAME}.key" \
              "virtual=yes" \
              "service-type=org.freedesktop.NetworkManager.strongswan" \
              )

    # Append each VPN option into VPN profile
    for option in "${VPN_OPTIONS[@]}"; do
        nmcli connection modify "$CONNECTION_NAME" \
              +vpn.data "${option}"
    done

}

main "$1" "$2" "$3" "$4"
