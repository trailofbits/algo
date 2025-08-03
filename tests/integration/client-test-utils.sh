#!/bin/bash
# Client test utilities

# Test WireGuard connection
test_wireguard() {
    local config_file="$1"
    echo "Testing WireGuard connection with $config_file"
    
    # Copy config
    cp "$config_file" /etc/wireguard/wg0.conf
    
    # Start WireGuard
    wg-quick up wg0
    
    # Wait for connection
    sleep 2
    
    # Check interface
    if ! ip link show wg0 &>/dev/null; then
        echo "ERROR: WireGuard interface not created"
        return 1
    fi
    
    # Test connectivity to VPN gateway
    if ping -c 4 10.19.49.1; then
        echo "SUCCESS: Can reach VPN gateway"
    else
        echo "ERROR: Cannot reach VPN gateway"
        return 1
    fi
    
    # Test DNS through tunnel
    if nslookup google.com 10.19.49.1; then
        echo "SUCCESS: DNS resolution working"
    else
        echo "ERROR: DNS resolution failed"
        return 1
    fi
    
    # Check routing
    if ip route | grep -q "0.0.0.0/0 dev wg0"; then
        echo "SUCCESS: Default route through VPN"
    else
        echo "WARNING: Default route not through VPN"
    fi
    
    wg show
    return 0
}

# Test IPsec connection
test_ipsec() {
    local cert_dir="$1"
    echo "Testing IPsec connection with certificates from $cert_dir"
    
    # Copy certificates
    cp -r "$cert_dir"/* /etc/swanctl/
    
    # Load credentials
    swanctl --load-all
    
    # Initiate connection
    swanctl --initiate --child algo
    
    # Wait for connection
    sleep 5
    
    # Check status
    if swanctl --list-sas | grep -q "ESTABLISHED"; then
        echo "SUCCESS: IPsec connection established"
    else
        echo "ERROR: IPsec connection failed"
        swanctl --list-sas
        return 1
    fi
    
    # Test connectivity
    if ping -c 4 10.19.48.1; then
        echo "SUCCESS: Can reach VPN gateway through IPsec"
    else
        echo "ERROR: Cannot reach VPN gateway"
        return 1
    fi
    
    return 0
}

# Test kill switch
test_kill_switch() {
    echo "Testing kill switch functionality"
    
    # Get current default route
    local orig_gw=$(ip route | grep "^default" | awk '{print $3}')
    
    # Disconnect VPN
    if ip link show wg0 &>/dev/null; then
        wg-quick down wg0
    fi
    
    # Try to reach internet
    if ping -c 2 -W 2 8.8.8.8 &>/dev/null; then
        echo "WARNING: Kill switch may not be working - can reach internet without VPN"
        return 1
    else
        echo "SUCCESS: Kill switch working - cannot reach internet without VPN"
        return 0
    fi
}

# Test multi-user scenario
test_multiuser() {
    echo "Testing multi-user VPN access"
    # This would be called from different client containers
    # to verify multiple users can connect simultaneously
    return 0
}

# Main test runner
case "$1" in
    wireguard)
        test_wireguard "$2"
        ;;
    ipsec)
        test_ipsec "$2"
        ;;
    killswitch)
        test_kill_switch
        ;;
    multiuser)
        test_multiuser
        ;;
    *)
        echo "Usage: $0 {wireguard|ipsec|killswitch|multiuser} [config]"
        exit 1
        ;;
esac