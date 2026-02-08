#!/usr/bin/env python3
"""List deployed Algo VPN servers as JSON."""

import json
import sys
from pathlib import Path

import yaml


def list_servers(configs_dir: Path) -> list[dict]:
    """Scan configs directory for deployed server metadata."""
    servers = []
    for config_file in sorted(configs_dir.glob("*/.config.yml")):
        with open(config_file) as f:
            config = yaml.safe_load(f)
        if config:
            servers.append(config)
    return servers


def main() -> None:
    configs_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("configs")
    if not configs_dir.is_dir():
        json.dump([], sys.stdout)
        print()
        sys.exit(0)
    servers = list_servers(configs_dir)
    json.dump(servers, sys.stdout, indent=2, default=str)
    print()


if __name__ == "__main__":
    main()
