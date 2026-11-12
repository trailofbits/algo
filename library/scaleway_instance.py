#!/usr/bin/python
"""Manage the Scaleway Instance API operations used by Algo."""

import json
import time
from typing import NoReturn
from urllib.parse import urlencode

from ansible.module_utils.basic import AnsibleModule, env_fallback
from ansible.module_utils.urls import fetch_url

DOCUMENTATION = r"""
---
module: scaleway_instance
short_description: Create, start, or delete an Algo Scaleway instance
description:
  - Uses the public zonal Instance API without collection-private helpers.
  - Finds instances by exact name and refuses ambiguous matches.
  - Deletion requires only the token, zone, and instance name.
author: Trail of Bits
options:
  api_token:
    description: Scaleway API token; defaults to SCW_TOKEN.
    type: str
    required: true
  zone:
    description: Full availability zone, such as nl-ams-2.
    type: str
    required: true
  name:
    description: Exact instance name.
    type: str
    required: true
  state:
    description: Desired instance state. Create with present before using running.
    type: str
    choices: [present, running, absent]
    default: present
  image:
    description: Marketplace image ID for a new instance.
    type: str
  commercial_type:
    description: Instance type for a new instance.
    type: str
  organization:
    description: Organization ID for a new instance.
    type: str
  tags:
    description: Instance tags, including Algo's SSH public key.
    type: list
    elements: str
    default: []
  wait_timeout:
    description: Maximum seconds to wait for an operation to complete.
    type: int
    default: 300
"""

EXAMPLES = r"""
- name: Delete an Algo instance
  scaleway_instance:
    zone: nl-ams-2
    name: algo
    state: absent
"""

RETURN = r"""
server:
  description: Latest Instance API server object, or an empty object after deletion.
  returned: always
  type: dict
"""


ZONES = [f"{region}-{number}" for region in ("fr-par", "nl-ams", "pl-waw") for number in (1, 2, 3)]
TRANSITIONS = {"starting", "stopping", "pending"}


class ScalewayInstance:
    """Apply Algo's instance lifecycle through the public Scaleway HTTP API."""

    def __init__(self, module: AnsibleModule) -> None:
        self.module = module
        self.params = module.params
        self.base = f"https://api.scaleway.com/instance/v1/zones/{self.params['zone']}"

    def fail(self, message: str) -> NoReturn:
        """Report the affected server and zone without disclosing credentials."""
        instance = f"Scaleway instance {self.params['name']} in {self.params['zone']}"
        self.module.fail_json(msg=f"{instance}: {message}")

    def request(self, method: str, path: str, *, body: dict | None = None) -> dict:
        """Send a request and reject failed or malformed responses."""
        response, info = fetch_url(
            self.module,
            f"{self.base}/{path}",
            method=method,
            data=json.dumps(body) if body is not None else None,
            headers={"X-Auth-Token": self.params["api_token"], "Content-Type": "application/json"},
            timeout=30,
        )
        status = info["status"]
        if method == "DELETE" and status in {204, 404}:
            return {}
        if not 200 <= status < 300:
            self.fail(f"{method} {path} failed (HTTP {status}); check token, zone and permissions.")
        try:
            data = json.loads(response.read()) if response is not None else None
        except (ValueError, UnicodeDecodeError):
            self.fail(f"{method} {path} returned invalid JSON; check the API status and retry.")
        if not isinstance(data, dict):
            self.fail(f"{method} {path} returned no JSON object; check Scaleway's API status.")
        return data

    def server(self, data: dict) -> dict:
        """Validate the resource required by subsequent lifecycle operations."""
        server = data.get("server")
        identifier = server.get("id") if isinstance(server, dict) else None
        if not isinstance(server, dict) or not isinstance(identifier, str) or not identifier:
            self.fail("the API returned no server ID; check Scaleway's API status before retrying.")
        return server

    def find(self) -> dict | None:
        """Search every page and refuse to modify instances with ambiguous names."""
        matches = []
        page = 1
        deadline = time.monotonic() + self.params["wait_timeout"]
        while time.monotonic() < deadline:
            query = urlencode({"name": self.params["name"], "per_page": 100, "page": page})
            data = self.request("GET", f"servers?{query}")
            servers = data.get("servers")
            if not isinstance(servers, list) or any(not isinstance(item, dict) for item in servers):
                self.fail("listing servers returned an invalid list; check Scaleway's API status.")
            matches.extend(item for item in servers if item.get("name") == self.params["name"])
            if len(matches) > 1:
                self.fail("multiple servers have this name; assign unique names and retry.")
            if len(servers) < 100:
                return self.server({"server": matches[0]}) if matches else None
            page += 1
        self.fail("listing servers timed out; check API availability and retry.")

    def wait(self, server: dict, expected: str | None = None) -> dict:
        """Wait for a stable state, returning the latest addresses and server attributes."""
        deadline = time.monotonic() + self.params["wait_timeout"]
        while True:
            state = server.get("state")
            if not isinstance(state, str):
                self.fail("the API returned an invalid state; check the instance in the console.")
            if state in {"running", "stopped"} and expected in {None, state}:
                return server
            if state not in TRANSITIONS | {"running", "stopped"}:
                self.fail(f"unexpected state {state!r}; check the instance in the console.")
            if time.monotonic() >= deadline:
                self.fail("the state transition timed out; check the instance in the console.")
            time.sleep(3)
            server = self.server(self.request("GET", f"servers/{server['id']}"))

    def action(self, server: dict, action: str, expected: str) -> dict:
        """Perform a power action and verify the final state."""
        path = f"servers/{server['id']}"
        self.request("POST", f"{path}/action", body={"action": action})
        return self.wait(self.server(self.request("GET", path)), expected)

    def create(self) -> dict:
        """Validate the selected image and create an instance with Algo's network settings."""
        image = self.request("GET", f"images/{self.params['image']}").get("image")
        if not isinstance(image, dict) or image.get("id") != self.params["image"]:
            self.fail(f"cannot read image {self.params['image']}; verify the image ID and zone.")
        keys = ("name", "image", "organization", "commercial_type")
        body = {key: self.params[key] for key in keys}
        body.update(
            tags=self.params["tags"],
            enable_ipv6=True,
            dynamic_ip_required=True,
            boot_type="local",
        )
        return self.wait(self.server(self.request("POST", "servers", body=body)))

    def present(self, server: dict | None) -> tuple[bool, dict]:
        """Ensure Algo tags and a public IPv4 address without replacing an existing disk."""
        if server is None:
            return True, {} if self.module.check_mode else self.create()
        desired = {"tags": self.params["tags"], "dynamic_ip_required": True}
        body = {key: value for key, value in desired.items() if server.get(key) != value}
        changed = bool(body)
        if changed and not self.module.check_mode:
            server = self.wait(server)
            server = self.server(self.request("PATCH", f"servers/{server['id']}", body=body))
        return changed, server

    def running(self, server: dict | None) -> tuple[bool, dict]:
        """Start an existing instance, including one already in transition."""
        if server is None:
            self.fail("the server does not exist; create it with state=present before starting it.")
        if self.module.check_mode:
            return server.get("state") != "running", server
        server = self.wait(server)
        if server["state"] == "running":
            return False, server
        return True, self.action(server, "poweron", "running")

    def absent(self, server: dict | None) -> tuple[bool, dict]:
        """Stop and delete an instance without consulting its original image."""
        if server is None:
            return False, {}
        if not self.module.check_mode:
            server = self.wait(server)
            if server["state"] == "running":
                server = self.action(server, "poweroff", "stopped")
            self.request("DELETE", f"servers/{server['id']}")
        return True, {}


def main() -> None:
    """Validate Ansible arguments and apply the requested lifecycle operation."""
    module = AnsibleModule(
        argument_spec={
            "api_token": {
                "type": "str",
                "required": True,
                "no_log": True,
                "fallback": (env_fallback, ["SCW_TOKEN"]),
            },
            "zone": {"type": "str", "required": True, "choices": ZONES},
            "name": {"type": "str", "required": True},
            "state": {"choices": ["present", "running", "absent"], "default": "present"},
            "image": {"type": "str"},
            "commercial_type": {"type": "str"},
            "organization": {"type": "str"},
            "tags": {"type": "list", "elements": "str", "default": []},
            "wait_timeout": {"type": "int", "default": 300},
        },
        required_if=[("state", "present", ["image", "commercial_type", "organization"])],
        supports_check_mode=True,
    )
    api = ScalewayInstance(module)
    if not module.params["name"] or module.params["wait_timeout"] <= 0:
        api.fail("provide a nonempty name and a positive wait_timeout.")
    server = api.find()
    operations = {"present": api.present, "running": api.running, "absent": api.absent}
    changed, server = operations[module.params["state"]](server)
    module.exit_json(changed=changed, server=server)


if __name__ == "__main__":
    main()
