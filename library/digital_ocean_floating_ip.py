#!/usr/bin/python
#
# (c) 2015, Patrick F. Marques <patrickfmarques@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)



ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: digital_ocean_floating_ip
short_description: Manage DigitalOcean Floating IPs
description:
     - Create/delete/assign a floating IP.
version_added: "2.4"
author: "Patrick Marques (@pmarques)"
options:
  state:
    description:
     - Indicate desired state of the target.
    default: present
    choices: ['present', 'absent']
  ip:
    description:
     - Public IP address of the Floating IP. Used to remove an IP
  region:
    description:
     - The region that the Floating IP is reserved to.
  droplet_id:
    description:
     - The Droplet that the Floating IP has been assigned to.
  oauth_token:
    description:
     - DigitalOcean OAuth token.
    required: true
notes:
  - Version 2 of DigitalOcean API is used.
requirements:
  - "python >= 2.6"
'''


EXAMPLES = '''
- name: "Create a Floating IP in region lon1"
  digital_ocean_floating_ip:
    state: present
    region: lon1

- name: "Create a Floating IP assigned to Droplet ID 123456"
  digital_ocean_floating_ip:
    state: present
    droplet_id: 123456

- name: "Delete a Floating IP with ip 1.2.3.4"
  digital_ocean_floating_ip:
    state: absent
    ip: "1.2.3.4"

'''


RETURN = '''
# Digital Ocean API info https://developers.digitalocean.com/documentation/v2/#floating-ips
data:
    description: a DigitalOcean Floating IP resource
    returned: success and no resource constraint
    type: dict
    sample: {
      "action": {
        "id": 68212728,
        "status": "in-progress",
        "type": "assign_ip",
        "started_at": "2015-10-15T17:45:44Z",
        "completed_at": null,
        "resource_id": 758603823,
        "resource_type": "floating_ip",
        "region": {
          "name": "New York 3",
          "slug": "nyc3",
          "sizes": [
            "512mb",
            "1gb",
            "2gb",
            "4gb",
            "8gb",
            "16gb",
            "32gb",
            "48gb",
            "64gb"
          ],
          "features": [
            "private_networking",
            "backups",
            "ipv6",
            "metadata"
          ],
          "available": true
        },
        "region_slug": "nyc3"
      }
    }
'''

import json
import time

from ansible.module_utils.basic import AnsibleModule, env_fallback
from ansible.module_utils.digital_ocean import DigitalOceanHelper


class Response:

    def __init__(self, resp, info):
        self.body = None
        if resp:
            self.body = resp.read()
        self.info = info

    @property
    def json(self):
        if not self.body:
            if "body" in self.info:
                return json.loads(self.info["body"])
            return None
        try:
            return json.loads(self.body)
        except ValueError:
            return None

    @property
    def status_code(self):
        return self.info["status"]

def wait_action(module, rest, ip, action_id, timeout=10):
    end_time = time.time() + 10
    while time.time() < end_time:
        response = rest.get(f'floating_ips/{ip}/actions/{action_id}')
        status_code = response.status_code
        status = response.json['action']['status']
        # TODO: check status_code == 200?
        if status == 'completed':
            return True
        elif status == 'errored':
            module.fail_json(msg=f'Floating ip action error [ip: {ip}: action: {action_id}]', data=json)

    module.fail_json(msg=f'Floating ip action timeout [ip: {ip}: action: {action_id}]', data=json)


def core(module):
    api_token = module.params['oauth_token']
    state = module.params['state']
    ip = module.params['ip']
    droplet_id = module.params['droplet_id']

    rest = DigitalOceanHelper(module)

    if state in ('present'):
        if droplet_id is not None and module.params['ip'] is not None:
            # Lets try to associate the ip to the specified droplet
            associate_floating_ips(module, rest)
        else:
            create_floating_ips(module, rest)

    elif state in ('absent'):
        response = rest.delete(f"floating_ips/{ip}")
        status_code = response.status_code
        json_data = response.json
        if status_code == 204:
            module.exit_json(changed=True)
        elif status_code == 404:
            module.exit_json(changed=False)
        else:
            module.exit_json(changed=False, data=json_data)


def get_floating_ip_details(module, rest):
    ip = module.params['ip']

    response = rest.get(f"floating_ips/{ip}")
    status_code = response.status_code
    json_data = response.json
    if status_code == 200:
        return json_data['floating_ip']
    else:
        module.fail_json(msg="Error assigning floating ip [{0}: {1}]".format(
            status_code, json_data["message"]), region=module.params['region'])


def assign_floating_id_to_droplet(module, rest):
    ip = module.params['ip']

    payload = {
        "type": "assign",
        "droplet_id": module.params['droplet_id'],
    }

    response = rest.post(f"floating_ips/{ip}/actions", data=payload)
    status_code = response.status_code
    json_data = response.json
    if status_code == 201:
        wait_action(module, rest, ip, json_data['action']['id'])

        module.exit_json(changed=True, data=json_data)
    else:
        module.fail_json(msg="Error creating floating ip [{0}: {1}]".format(
            status_code, json_data["message"]), region=module.params['region'])


def associate_floating_ips(module, rest):
    floating_ip = get_floating_ip_details(module, rest)
    droplet = floating_ip['droplet']

    # TODO: If already assigned to a droplet verify if is one of the specified as valid
    if droplet is not None and str(droplet['id']) in [module.params['droplet_id']]:
        module.exit_json(changed=False)
    else:
        assign_floating_id_to_droplet(module, rest)


def create_floating_ips(module, rest):
    payload = {
    }
    floating_ip_data = None

    if module.params['region'] is not None:
        payload["region"] = module.params['region']

    if module.params['droplet_id'] is not None:
        payload["droplet_id"] = module.params['droplet_id']

    floating_ips = rest.get_paginated_data(base_url='floating_ips?', data_key_name='floating_ips')

    for floating_ip in floating_ips:
        if floating_ip['droplet'] and floating_ip['droplet']['id'] == module.params['droplet_id']:
            floating_ip_data = {'floating_ip': floating_ip}

    if floating_ip_data:
        module.exit_json(changed=False, data=floating_ip_data)
    else:
        response = rest.post("floating_ips", data=payload)
        status_code = response.status_code
        json_data = response.json

        if status_code == 202:
            module.exit_json(changed=True, data=json_data)
        else:
            module.fail_json(msg="Error creating floating ip [{0}: {1}]".format(
                status_code, json_data["message"]), region=module.params['region'])


def main():
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(choices=['present', 'absent'], default='present'),
            ip=dict(aliases=['id'], required=False),
            region=dict(required=False),
            droplet_id=dict(required=False, type='int'),
            oauth_token=dict(
                no_log=True,
                # Support environment variable for DigitalOcean OAuth Token
                fallback=(env_fallback, ['DO_API_TOKEN', 'DO_API_KEY', 'DO_OAUTH_TOKEN']),
                required=True,
            ),
            validate_certs=dict(type='bool', default=True),
            timeout=dict(type='int', default=30),
        ),
        required_if=[
            ('state', 'delete', ['ip'])
        ],
        mutually_exclusive=[
            ['region', 'droplet_id']
        ],
    )

    core(module)


if __name__ == '__main__':
    main()
