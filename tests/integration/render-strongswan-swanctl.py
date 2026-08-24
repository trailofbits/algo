#!/usr/bin/env python3
"""Render deterministic, non-secret StrongSwan configs for native parser tests."""

import argparse
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--templates", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    environment = Environment(loader=FileSystemLoader(args.templates), undefined=StrictUndefined)
    environment.filters["bool"] = bool
    values = {
        "IP_subject_alt_name": "10.99.0.1",
        "strongswan_log_level": "-1",
        "strongswan_network": "10.48.0.0/16",
        "strongswan_network_ipv6": "2001:db8:4160::/48",
        "local_service_ip": "172.16.0.10",
        "local_service_ipv6": "fd00::10",
        "algo_dns_adblocking": True,
        "dns_encryption": False,
        "dns_servers": {
            "ipv4": ["1.1.1.1", "1.0.0.1"],
            "ipv6": ["2606:4700:4700::1111", "2606:4700:4700::1001"],
        },
        "ciphers": {
            "defaults": {
                "ike": "aes256gcm16-prfsha512-ecp384!",
                "esp": "aes256gcm16-ecp384!",
            }
        },
    }
    args.output.mkdir(parents=True, exist_ok=True)
    for template_name, output_name in (
        ("swanctl.conf.j2", "swanctl.conf"),
        ("strongswan.conf.j2", "strongswan.conf"),
    ):
        rendered = environment.get_template(template_name).render(**values)
        (args.output / output_name).write_text(rendered + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
