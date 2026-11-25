#!/usr/bin/python
"""List Compute Engine regions or zones with the installed Google collection."""

from ansible_collections.google.cloud.plugins.module_utils.gcp_utils import GcpModule, GcpSession

DOCUMENTATION = """
module: gcp_compute_location_info
short_description: List Compute Engine regions or zones
description: Lists the regions or zones visible to the authenticated Google Cloud project.
extends_documentation_fragment:
  - google.cloud.gcp
  - google.cloud.info
options:
  scope:
    description: The type of location to list.
    type: str
    required: true
    choices: [regions, zones]
"""

EXAMPLES = """
- name: List available Compute Engine regions
  gcp_compute_location_info:
    project: example-project
    auth_kind: application
    scope: regions
"""

RETURN = """
resources:
  description: Locations returned by Compute Engine.
  type: list
  elements: dict
  returned: success
"""


def location_page(module, response):
    """Read one list response, including empty pages and Google API errors."""
    if response.status_code in (204, 404):
        return {}
    module.raise_for_status(response)
    try:
        result = response.json()
    except ValueError as error:
        module.fail_json(msg=f"Invalid JSON listing GCE locations: {error}")
    if result.get("error"):
        module.fail_json(msg=result["error"])
    return result


def main():
    """Return every matching GCE location, following the API's page tokens."""
    module = GcpModule(
        argument_spec={
            "filters": {"type": "list", "elements": "str", "default": []},
            "scope": {"required": True, "type": "str", "choices": ["regions", "zones"]},
        },
        supports_check_mode=True,
    )
    if not module.params["scopes"]:
        module.params["scopes"] = ["https://www.googleapis.com/auth/compute"]
    filters = module.params["filters"]
    if len(filters) > 1:
        filters = [term if term.startswith("(") and term.endswith(")") else f"({term})" for term in filters]
    query = " ".join(filters)
    url = "https://compute.googleapis.com/compute/v1/projects/{project}/{scope}".format(**module.params)
    resources = GcpSession(module, "compute").list(url, location_page, params={"filter": query})
    module.exit_json(resources=resources)


if __name__ == "__main__":
    main()
