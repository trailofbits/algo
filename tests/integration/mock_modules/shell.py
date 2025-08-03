#!/usr/bin/python
# Mock shell module for Docker testing

import subprocess

from ansible.module_utils.basic import AnsibleModule


def main():
    module = AnsibleModule(
        argument_spec=dict(
            _raw_params=dict(type='str'),
            cmd=dict(type='str'),
            creates=dict(type='path'),
            removes=dict(type='path'),
            chdir=dict(type='path'),
            executable=dict(type='path', default='/bin/sh'),
            warn=dict(type='bool', default=False),
            stdin=dict(type='str'),
            stdin_add_newline=dict(type='bool', default=True),
        ),
        supports_check_mode=True
    )

    # Get the command
    raw_params = module.params.get('_raw_params')
    cmd = module.params.get('cmd') or raw_params

    if not cmd:
        module.fail_json(msg="no command given")

    result = dict(
        changed=False,
        cmd=cmd,
        rc=0,
        stdout='',
        stderr='',
        stdout_lines=[],
        stderr_lines=[]
    )

    # Log the operation
    with open('/var/log/mock-shell-module.log', 'a') as f:
        f.write(f"shell module called: cmd={cmd}\n")

    # Handle specific commands
    if 'echo 1 > /proc/sys/net/ipv4/route/flush' in cmd:
        # Routing cache flush - just pretend it worked
        result['stdout'] = ""
        result['changed'] = True
    elif 'ifconfig lo100' in cmd:
        # BSD loopback commands - simulate success
        result['stdout'] = "0"
        result['changed'] = True
    else:
        # For other commands, try to run them
        try:
            proc = subprocess.run(cmd, shell=True, capture_output=True, text=True,
                                executable=module.params.get('executable'),
                                cwd=module.params.get('chdir'))
            result['rc'] = proc.returncode
            result['stdout'] = proc.stdout
            result['stderr'] = proc.stderr
            result['stdout_lines'] = proc.stdout.splitlines()
            result['stderr_lines'] = proc.stderr.splitlines()
            result['changed'] = True
        except Exception as e:
            result['rc'] = 1
            result['stderr'] = str(e)
            result['msg'] = str(e)
            module.fail_json(msg=result['msg'], **result)

    if result['rc'] == 0:
        module.exit_json(**result)
    else:
        if 'msg' not in result:
            result['msg'] = f"Command failed with return code {result['rc']}"
        module.fail_json(msg=result['msg'], **result)

if __name__ == '__main__':
    main()
