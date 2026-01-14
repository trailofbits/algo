#!/usr/bin/python
# Mock command module for Docker testing

import subprocess

from ansible.module_utils.basic import AnsibleModule


def main():
    module = AnsibleModule(
        argument_spec={
            "_raw_params": {"type": "str"},
            "cmd": {"type": "str"},
            "creates": {"type": "path"},
            "removes": {"type": "path"},
            "chdir": {"type": "path"},
            "executable": {"type": "path"},
            "warn": {"type": "bool", "default": False},
            "stdin": {"type": "str"},
            "stdin_add_newline": {"type": "bool", "default": True},
            "strip_empty_ends": {"type": "bool", "default": True},
            "_uses_shell": {"type": "bool", "default": False},
        },
        supports_check_mode=True,
    )

    # Get the command
    raw_params = module.params.get("_raw_params")
    cmd = module.params.get("cmd") or raw_params

    if not cmd:
        module.fail_json(msg="no command given")

    result = {"changed": False, "cmd": cmd, "rc": 0, "stdout": "", "stderr": "", "stdout_lines": [], "stderr_lines": []}

    # Log the operation
    with open("/var/log/mock-command-module.log", "a") as f:
        f.write(f"command module called: cmd={cmd}\n")

    # Handle specific commands
    if "apparmor_status" in cmd:
        # Pretend apparmor is not installed/active
        result["rc"] = 127
        result["stderr"] = "apparmor_status: command not found"
        result["msg"] = "[Errno 2] No such file or directory: b'apparmor_status'"
        module.fail_json(msg=result["msg"], **result)
    elif "netplan apply" in cmd:
        # Pretend netplan succeeded
        result["stdout"] = "Mock: netplan configuration applied"
        result["changed"] = True
    elif "echo 1 > /proc/sys/net/ipv4/route/flush" in cmd:
        # Routing cache flush
        result["stdout"] = "1"
        result["changed"] = True
    else:
        # For other commands, try to run them
        try:
            proc = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=module.params.get("chdir"))
            result["rc"] = proc.returncode
            result["stdout"] = proc.stdout
            result["stderr"] = proc.stderr
            result["stdout_lines"] = proc.stdout.splitlines()
            result["stderr_lines"] = proc.stderr.splitlines()
            result["changed"] = True
        except Exception as e:
            result["rc"] = 1
            result["stderr"] = str(e)
            result["msg"] = str(e)
            module.fail_json(msg=result["msg"], **result)

    if result["rc"] == 0:
        module.exit_json(**result)
    else:
        if "msg" not in result:
            result["msg"] = f"Command failed with return code {result['rc']}"
        module.fail_json(msg=result["msg"], **result)


if __name__ == "__main__":
    main()
