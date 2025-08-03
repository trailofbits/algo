#!/usr/bin/python
# Mock service module for Docker testing

from ansible.module_utils.basic import AnsibleModule
import subprocess

def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(required=True, type='str'),
            state=dict(type='str', choices=['started', 'stopped', 'restarted', 'reloaded'], default='started'),
            enabled=dict(type='bool'),
            pattern=dict(type='str'),
            arguments=dict(type='str', aliases=['args']),
        ),
        supports_check_mode=True
    )
    
    name = module.params['name']
    state = module.params['state']
    enabled = module.params['enabled']
    
    result = dict(
        changed=False,
        name=name,
        state=state
    )
    
    # Log the operation
    with open('/var/log/mock-service-module.log', 'a') as f:
        f.write(f"service module called: name={name}, state={state}, enabled={enabled}\n")
    
    # Handle state changes
    if state:
        cmd_map = {
            'started': 'start',
            'stopped': 'stop',
            'restarted': 'restart',
            'reloaded': 'reload'
        }
        
        if state in cmd_map:
            # Use our mock systemctl
            cmd = ['/usr/bin/systemctl', cmd_map[state], name]
            rc = subprocess.run(cmd, capture_output=True, text=True)
            result['changed'] = True
    
    # Handle enabled/disabled 
    if enabled is not None:
        cmd = ['/usr/bin/systemctl', 'enable' if enabled else 'disable', name]
        subprocess.run(cmd, check=False)
        result['changed'] = True
        result['enabled'] = enabled
    
    module.exit_json(**result)

if __name__ == '__main__':
    main()