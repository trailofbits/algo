#!/usr/bin/python
"""Close Algo IKE sessions belonging to retired certificate identities."""

import re

from ansible.module_utils.basic import AnsibleModule

# stroke prints the IKE ID and both authenticated identities on the SA header.
SA = re.compile(r"^\s*ikev2-pubkey\[([0-9]+)\]: [^,\n]+, [^\n]*?\]\.\.\.[^\[\n]+\[([^\]\n]+)\]$", re.MULTILINE)


def retired_sessions(status: str, names: list[str], domain: str) -> list[str]:
    """Return unique IKE handles for the retired Algo certificate identities."""
    identities = {identity for name in names for identity in (name, f"CN={name}", f"{name}@{domain}")}
    return [f"ikev2-pubkey[{number}]" for number, peer in SA.findall(status) if peer in identities]


def main() -> None:
    """Read active SAs from stroke and terminate each matching IKE handle."""
    module = AnsibleModule(
        argument_spec={
            "retired": {"type": "list", "elements": "str", "required": True},
            "domain": {"type": "str", "required": True},
        },
        supports_check_mode=True,
    )
    ipsec = module.get_bin_path("ipsec", required=True)

    def remaining() -> list[str]:
        _, status, _ = module.run_command([ipsec, "status"], check_rc=True)
        return retired_sessions(status, module.params["retired"], module.params["domain"])

    matches = remaining()
    if matches and not module.check_mode:
        for handle in matches:
            # A peer can disconnect between enumeration and the command.
            module.run_command([ipsec, "down", handle])
        if remaining():
            module.fail_json(msg="Some retired IPsec sessions remain active. Retry the user update.")
    module.exit_json(changed=bool(matches), matched=len(matches))


if __name__ == "__main__":
    main()
