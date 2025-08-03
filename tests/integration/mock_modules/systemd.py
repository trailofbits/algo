#!/usr/bin/python
# Mock systemd module for Docker testing

from ansible.module_utils.basic import AnsibleModule
import subprocess
import os

def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(required=True, type='str'),
            state=dict(type='str', choices=['started', 'stopped', 'restarted', 'reloaded'], default='started'),
            enabled=dict(type='bool'),
            daemon_reload=dict(type='bool', default=False),
            daemon_reexec=dict(type='bool', default=False),
            masked=dict(type='bool'),
        ),
        supports_check_mode=True
    )
    
    name = module.params['name']
    state = module.params['state']
    enabled = module.params['enabled']
    daemon_reload = module.params['daemon_reload']
    
    result = dict(
        changed=False,
        name=name,
        state=state,
        status={}
    )
    
    # Log the operation
    with open('/var/log/mock-systemd-module.log', 'a') as f:
        f.write(f"systemd module called: name={name}, state={state}, enabled={enabled}\n")
    
    # Daemon reload
    if daemon_reload:
        subprocess.run(['/usr/bin/systemctl', 'daemon-reload'], check=False)
        result['changed'] = True
    
    # Handle state changes
    if state:
        cmd_map = {
            'started': 'start',
            'stopped': 'stop', 
            'restarted': 'restart',
            'reloaded': 'reload'
        }
        
        if state in cmd_map:
            cmd = ['/usr/bin/systemctl', cmd_map[state], name]
            rc = subprocess.run(cmd, capture_output=True, text=True)
            
            if rc.returncode == 0:
                result['changed'] = True
                result['status'] = {
                    'ActiveState': 'active' if state in ['started', 'restarted', 'reloaded'] else 'inactive',
                    'LoadState': 'loaded',
                    'SubState': 'running' if state in ['started', 'restarted', 'reloaded'] else 'dead'
                }
            else:
                # Even if systemctl fails, we pretend it worked for testing
                result['changed'] = True
                result['status'] = {
                    'ActiveState': 'active',
                    'LoadState': 'loaded', 
                    'SubState': 'running'
                }
    
    # Handle enabled/disabled
    if enabled is not None:
        cmd = ['/usr/bin/systemctl', 'enable' if enabled else 'disable', name]
        subprocess.run(cmd, check=False)
        result['changed'] = True
        result['enabled'] = enabled
    
    module.exit_json(**result)

if __name__ == '__main__':
    main()