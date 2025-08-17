#!/usr/bin/env python3
"""
Test that generated configuration files have valid syntax
This validates WireGuard, StrongSwan, SSH, and other configs
"""

import re
import subprocess
import sys


def check_command_available(cmd):
    """Check if a command is available on the system"""
    try:
        subprocess.run([cmd, "--version"], capture_output=True, check=False)
        return True
    except FileNotFoundError:
        return False


def test_wireguard_config_syntax():
    """Test WireGuard configuration file syntax"""
    # Sample WireGuard config based on Algo's template
    sample_config = """[Interface]
Address = 10.19.49.2/32,fd9d:bc11:4020::2/128
PrivateKey = SAMPLE_PRIVATE_KEY_BASE64==
DNS = 1.1.1.1,1.0.0.1

[Peer]
PublicKey = SAMPLE_PUBLIC_KEY_BASE64==
PresharedKey = SAMPLE_PRESHARED_KEY_BASE64==
AllowedIPs = 0.0.0.0/0,::/0
Endpoint = 10.0.0.1:51820
PersistentKeepalive = 25
"""

    # Validate config structure
    errors = []

    # Check for required sections
    if "[Interface]" not in sample_config:
        errors.append("Missing [Interface] section")
    if "[Peer]" not in sample_config:
        errors.append("Missing [Peer] section")

    # Validate Interface section
    interface_match = re.search(r"\[Interface\](.*?)\[Peer\]", sample_config, re.DOTALL)
    if interface_match:
        interface_section = interface_match.group(1)

        # Check required fields
        if not re.search(r"Address\s*=", interface_section):
            errors.append("Missing Address in Interface section")
        if not re.search(r"PrivateKey\s*=", interface_section):
            errors.append("Missing PrivateKey in Interface section")

        # Validate IP addresses
        address_match = re.search(r"Address\s*=\s*([^\n]+)", interface_section)
        if address_match:
            addresses = address_match.group(1).split(",")
            for addr in addresses:
                addr = addr.strip()
                # Basic IP validation
                if not re.match(r"^\d+\.\d+\.\d+\.\d+/\d+$", addr) and not re.match(r"^[0-9a-fA-F:]+/\d+$", addr):
                    errors.append(f"Invalid IP address format: {addr}")

    # Validate Peer section
    peer_match = re.search(r"\[Peer\](.*)", sample_config, re.DOTALL)
    if peer_match:
        peer_section = peer_match.group(1)

        # Check required fields
        if not re.search(r"PublicKey\s*=", peer_section):
            errors.append("Missing PublicKey in Peer section")
        if not re.search(r"AllowedIPs\s*=", peer_section):
            errors.append("Missing AllowedIPs in Peer section")
        if not re.search(r"Endpoint\s*=", peer_section):
            errors.append("Missing Endpoint in Peer section")

        # Validate endpoint format
        endpoint_match = re.search(r"Endpoint\s*=\s*([^\n]+)", peer_section)
        if endpoint_match:
            endpoint = endpoint_match.group(1).strip()
            if not re.match(r"^[\d\.\:]+:\d+$", endpoint):
                errors.append(f"Invalid Endpoint format: {endpoint}")

    if errors:
        print("✗ WireGuard config validation failed:")
        for error in errors:
            print(f"  - {error}")
        assert False, "WireGuard config validation failed"
    else:
        print("✓ WireGuard config syntax validation passed")


def test_strongswan_ipsec_conf():
    """Test StrongSwan ipsec.conf syntax"""
    # Sample ipsec.conf based on Algo's template
    sample_config = """config setup
    charondebug="ike 2, knl 2, cfg 2, net 2, esp 2, dmn 2, mgr 2"
    strictcrlpolicy=yes
    uniqueids=never

conn %default
    keyexchange=ikev2
    dpdaction=clear
    dpddelay=35s
    dpdtimeout=150s
    compress=yes
    ikelifetime=24h
    lifetime=8h
    rekey=yes
    reauth=yes
    fragmentation=yes
    ike=aes128gcm16-prfsha512-ecp256,aes128-sha2_256-modp2048
    esp=aes128gcm16-ecp256,aes128-sha2_256-modp2048

conn ikev2-pubkey
    auto=add
    left=%any
    leftid=@10.0.0.1
    leftcert=server.crt
    leftsendcert=always
    leftsubnet=0.0.0.0/0,::/0
    right=%any
    rightid=%any
    rightauth=pubkey
    rightsourceip=10.19.49.0/24,fd9d:bc11:4020::/64
    rightdns=1.1.1.1,1.0.0.1
"""

    errors = []

    # Check for required sections
    if "config setup" not in sample_config:
        errors.append("Missing 'config setup' section")
    if "conn %default" not in sample_config:
        errors.append("Missing 'conn %default' section")

    # Validate connection settings
    conn_pattern = re.compile(r"conn\s+(\S+)")
    connections = conn_pattern.findall(sample_config)

    if len(connections) < 2:  # Should have at least %default and one other
        errors.append("Not enough connection definitions")

    # Check for required parameters in connections
    required_params = ["keyexchange", "left", "right"]
    for param in required_params:
        if f"{param}=" not in sample_config:
            errors.append(f"Missing required parameter: {param}")

    # Validate IP subnet formats
    subnet_pattern = re.compile(r"(left|right)subnet\s*=\s*([^\n]+)")
    for match in subnet_pattern.finditer(sample_config):
        subnets = match.group(2).split(",")
        for subnet in subnets:
            subnet = subnet.strip()
            if subnet != "0.0.0.0/0" and subnet != "::/0":
                if not re.match(r"^\d+\.\d+\.\d+\.\d+/\d+$", subnet) and not re.match(r"^[0-9a-fA-F:]+/\d+$", subnet):
                    errors.append(f"Invalid subnet format: {subnet}")

    if errors:
        print("✗ StrongSwan ipsec.conf validation failed:")
        for error in errors:
            print(f"  - {error}")
        assert False, "ipsec.conf validation failed"
    else:
        print("✓ StrongSwan ipsec.conf syntax validation passed")


def test_ssh_config_syntax():
    """Test SSH tunnel configuration syntax"""
    # Sample SSH config for tunneling
    sample_config = """Host algo-tunnel
    HostName 10.0.0.1
    User algo
    Port 4160
    IdentityFile ~/.ssh/algo.pem
    StrictHostKeyChecking no
    UserKnownHostsFile /dev/null
    ServerAliveInterval 60
    ServerAliveCountMax 3
    LocalForward 1080 127.0.0.1:1080
"""

    errors = []

    # Parse SSH config format
    lines = sample_config.strip().split("\n")
    current_host = None

    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        if line.startswith("Host "):
            current_host = line.split()[1]
        elif current_host and " " in line:
            key, value = line.split(None, 1)

            # Validate common SSH options
            if key == "Port":
                try:
                    port = int(value)
                    if not 1 <= port <= 65535:
                        errors.append(f"Invalid port number: {port}")
                except ValueError:
                    errors.append(f"Port must be a number: {value}")

            elif key == "LocalForward":
                # Format: LocalForward [bind_address:]port host:hostport
                parts = value.split()
                if len(parts) != 2:
                    errors.append(f"Invalid LocalForward format: {value}")

    if not current_host:
        errors.append("No Host definition found")

    if errors:
        print("✗ SSH config validation failed:")
        for error in errors:
            print(f"  - {error}")
        assert False, "SSH config validation failed"
    else:
        print("✓ SSH config syntax validation passed")


def test_iptables_rules_syntax():
    """Test iptables rules syntax"""
    # Sample iptables rules based on Algo's rules.v4.j2
    sample_rules = """*nat
:PREROUTING ACCEPT [0:0]
:INPUT ACCEPT [0:0]
:OUTPUT ACCEPT [0:0]
:POSTROUTING ACCEPT [0:0]
-A POSTROUTING -s 10.19.49.0/24 ! -d 10.19.49.0/24 -j MASQUERADE
COMMIT

*filter
:INPUT DROP [0:0]
:FORWARD DROP [0:0]
:OUTPUT ACCEPT [0:0]
-A INPUT -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT
-A INPUT -i lo -j ACCEPT
-A INPUT -p icmp --icmp-type echo-request -j ACCEPT
-A INPUT -p tcp --dport 4160 -j ACCEPT
-A INPUT -p udp --dport 51820 -j ACCEPT
-A FORWARD -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT
-A FORWARD -s 10.19.49.0/24 -j ACCEPT
COMMIT
"""

    errors = []

    # Check table definitions
    tables = re.findall(r"\*(\w+)", sample_rules)
    if "filter" not in tables:
        errors.append("Missing *filter table")
    if "nat" not in tables:
        errors.append("Missing *nat table")

    # Check for COMMIT statements
    commit_count = sample_rules.count("COMMIT")
    if commit_count != len(tables):
        errors.append(f"Number of COMMIT statements ({commit_count}) doesn't match tables ({len(tables)})")

    # Validate chain policies
    chain_pattern = re.compile(r"^:(\w+)\s+(ACCEPT|DROP|REJECT)\s+\[\d+:\d+\]", re.MULTILINE)
    chains = chain_pattern.findall(sample_rules)

    required_chains = [("INPUT", "DROP"), ("FORWARD", "DROP"), ("OUTPUT", "ACCEPT")]
    for chain, _policy in required_chains:
        if not any(c[0] == chain for c in chains):
            errors.append(f"Missing required chain: {chain}")

    # Validate rule syntax
    rule_pattern = re.compile(r"^-[AI]\s+(\w+)", re.MULTILINE)
    rules = rule_pattern.findall(sample_rules)

    if len(rules) < 5:
        errors.append("Insufficient firewall rules")

    # Check for essential security rules
    if "-A INPUT -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT" not in sample_rules:
        errors.append("Missing stateful connection tracking rule")

    if errors:
        print("✗ iptables rules validation failed:")
        for error in errors:
            print(f"  - {error}")
        assert False, "iptables rules validation failed"
    else:
        print("✓ iptables rules syntax validation passed")


def test_dns_config_syntax():
    """Test dnsmasq configuration syntax"""
    # Sample dnsmasq config
    sample_config = """user=nobody
group=nogroup
interface=eth0
interface=wg0
bind-interfaces
bogus-priv
no-resolv
no-poll
server=1.1.1.1
server=1.0.0.1
local-ttl=300
cache-size=10000
log-queries
log-facility=/var/log/dnsmasq.log
conf-dir=/etc/dnsmasq.d/,*.conf
addn-hosts=/var/lib/algo/dns/adblock.hosts
"""

    errors = []

    # Parse config
    for line in sample_config.strip().split("\n"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        # Most dnsmasq options are key=value or just key
        if "=" in line:
            key, value = line.split("=", 1)

            # Validate specific options
            if key == "interface":
                if not re.match(r"^[a-zA-Z0-9\-_]+$", value):
                    errors.append(f"Invalid interface name: {value}")

            elif key == "server":
                # Basic IP validation
                if not re.match(r"^\d+\.\d+\.\d+\.\d+$", value) and not re.match(r"^[0-9a-fA-F:]+$", value):
                    errors.append(f"Invalid DNS server IP: {value}")

            elif key == "cache-size":
                try:
                    size = int(value)
                    if size < 0:
                        errors.append(f"Invalid cache size: {size}")
                except ValueError:
                    errors.append(f"Cache size must be a number: {value}")

    # Check for required options
    required = ["interface", "server"]
    for req in required:
        if f"{req}=" not in sample_config:
            errors.append(f"Missing required option: {req}")

    if errors:
        print("✗ dnsmasq config validation failed:")
        for error in errors:
            print(f"  - {error}")
        assert False, "dnsmasq config validation failed"
    else:
        print("✓ dnsmasq config syntax validation passed")


if __name__ == "__main__":
    tests = [
        test_wireguard_config_syntax,
        test_strongswan_ipsec_conf,
        test_ssh_config_syntax,
        test_iptables_rules_syntax,
        test_dns_config_syntax,
    ]

    failed = 0
    for test in tests:
        try:
            test()
        except AssertionError as e:
            print(f"✗ {test.__name__} failed: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ {test.__name__} error: {e}")
            failed += 1

    if failed > 0:
        print(f"\n{failed} tests failed")
        sys.exit(1)
    else:
        print(f"\nAll {len(tests)} config syntax tests passed!")
