#!/usr/bin/env python3
"""
Wrapper for Ansible's service module that always succeeds for known services
"""

import json
import sys

# Parse module arguments
args = json.loads(sys.stdin.read())
module_args = args.get("ANSIBLE_MODULE_ARGS", {})

service_name = module_args.get("name", "")
state = module_args.get("state", "started")

# Known services that should always succeed
known_services = [
    "netfilter-persistent",
    "iptables",
    "wg-quick@wg0",
    "strongswan-starter",
    "ipsec",
    "apparmor",
    "unattended-upgrades",
    "systemd-networkd",
    "systemd-resolved",
    "rsyslog",
    "ipfw",
    "cron",
]

# Check if it's a known service
service_found = False
for svc in known_services:
    if service_name == svc or service_name.startswith(svc + "."):
        service_found = True
        break

if service_found:
    # Return success
    result = {
        "changed": True if state in ["started", "stopped", "restarted", "reloaded"] else False,
        "name": service_name,
        "state": state,
        "status": {
            "LoadState": "loaded",
            "ActiveState": "active" if state != "stopped" else "inactive",
            "SubState": "running" if state != "stopped" else "dead",
        },
    }
    print(json.dumps(result))
    sys.exit(0)
else:
    # Service not found
    error = {"failed": True, "msg": f"Could not find the requested service {service_name}: "}
    print(json.dumps(error))
    sys.exit(1)
