#!/usr/bin/python
# Mock apt module for Docker testing

import subprocess

from ansible.module_utils.basic import AnsibleModule


def main():
    module = AnsibleModule(
        argument_spec={
            "name": {"type": "list", "aliases": ["pkg", "package"]},
            "state": {
                "type": "str",
                "default": "present",
                "choices": ["present", "absent", "latest", "build-dep", "fixed"],
            },
            "update_cache": {"type": "bool", "default": False},
            "cache_valid_time": {"type": "int", "default": 0},
            "install_recommends": {"type": "bool"},
            "force": {"type": "bool", "default": False},
            "allow_unauthenticated": {"type": "bool", "default": False},
            "allow_downgrade": {"type": "bool", "default": False},
            "allow_change_held_packages": {"type": "bool", "default": False},
            "dpkg_options": {"type": "str", "default": "force-confdef,force-confold"},
            "autoremove": {"type": "bool", "default": False},
            "purge": {"type": "bool", "default": False},
            "force_apt_get": {"type": "bool", "default": False},
        },
        supports_check_mode=True,
    )

    name = module.params["name"]
    state = module.params["state"]
    update_cache = module.params["update_cache"]

    result = {"changed": False, "cache_updated": False, "cache_update_time": 0}

    # Log the operation
    with open("/var/log/mock-apt-module.log", "a") as f:
        f.write(f"apt module called: name={name}, state={state}, update_cache={update_cache}\n")

    # Handle cache update
    if update_cache:
        # In Docker, apt-get update was already run in entrypoint
        # Just pretend it succeeded
        result["cache_updated"] = True
        result["cache_update_time"] = 1754231778  # Fixed timestamp
        result["changed"] = True

    # Handle package installation/removal
    if name:
        packages = name if isinstance(name, list) else [name]

        # Check which packages are already installed
        installed_packages = []
        for pkg in packages:
            # Use dpkg to check if package is installed
            check_cmd = ["dpkg", "-s", pkg]
            rc = subprocess.run(check_cmd, capture_output=True)
            if rc.returncode == 0:
                installed_packages.append(pkg)

        if state in ["present", "latest"]:
            # Check if we need to install anything
            missing_packages = [p for p in packages if p not in installed_packages]

            if missing_packages:
                # Log what we would install
                with open("/var/log/mock-apt-module.log", "a") as f:
                    f.write(f"Would install packages: {missing_packages}\n")

                # For our test purposes, these packages are pre-installed in Docker
                # Just report success
                result["changed"] = True
                result["stdout"] = f"Mock: Packages {missing_packages} are already available"
                result["stderr"] = ""
            else:
                result["stdout"] = "All packages are already installed"

        elif state == "absent":
            # Check if we need to remove anything
            present_packages = [p for p in packages if p in installed_packages]

            if present_packages:
                result["changed"] = True
                result["stdout"] = f"Mock: Would remove packages {present_packages}"
            else:
                result["stdout"] = "No packages to remove"

    # Always report success for our testing
    module.exit_json(**result)


if __name__ == "__main__":
    main()
