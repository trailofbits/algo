#!/usr/bin/python
# -*- coding: utf-8 -*-
#

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.cloudstack import (
    AnsibleCloudStack,
    cs_argument_spec,
    cs_required_together,
)

DOCUMENTATION = '''
---
module: cloudstack_zones
short_description: List zones on Apache CloudStack based clouds.
description:
    - List zones.
version_added: '0.1'
author: Julien Bachmann (@0xmilkmix)
extends_documentation_fragment: cloudstack
'''

EXAMPLES = '''
- name: List zones
  cloudstack_zones:
  register: _cs_zones
'''

RETURN = '''
---
zone:
  description: List of zones.
  returned: success
  type: list
  sample:
     [
        {
        "allocationstate": "Enabled",
        "dhcpprovider": "VirtualRouter",
        "id": "1128bd56-b4d9-4ac6-a7b9-c715b187ce11",
        "localstorageenabled": true,
        "name": "ch-gva-2",
        "networktype": "Basic",
        "securitygroupsenabled": true,
        "tags": [],
        "zonetoken": "token"
        },
        {
        "allocationstate": "Enabled",
        "dhcpprovider": "VirtualRouter",
        "id": "91e5e9e4-c9ed-4b76-bee4-427004b3baf9",
        "localstorageenabled": true,
        "name": "ch-dk-2",
        "networktype": "Basic",
        "securitygroupsenabled": true,
        "tags": [],
        "zonetoken": "token"
        },
        {
        "allocationstate": "Enabled",
        "dhcpprovider": "VirtualRouter",
        "id": "4da1b188-dcd6-4ff5-b7fd-bde984055548",
        "localstorageenabled": true,
        "name": "at-vie-1",
        "networktype": "Basic",
        "securitygroupsenabled": true,
        "tags": [],
        "zonetoken": "token"
        },
        {
        "allocationstate": "Enabled",
        "dhcpprovider": "VirtualRouter",
        "id": "35eb7739-d19e-45f7-a581-4687c54d6d02",
        "localstorageenabled": true,
        "name": "de-fra-1",
        "networktype": "Basic",
        "securitygroupsenabled": true,
        "tags": [],
        "zonetoken": "token"
        }
    ]
'''

class AnsibleCloudStackZones(AnsibleCloudStack):

    def __init__(self, module):
        super(AnsibleCloudStackZones, self).__init__(module)
        self.zones = None

    def get_zones(self):
        args = {}
        if not self.zones:
            zones = self.query_api('listZones', **args)
            if zones:
                self.zones = zones
        return self.zones

def main():
    module = AnsibleModule(argument_spec={})
    acs_zones = AnsibleCloudStackZones(module)
    result = acs_zones.get_zones()
    module.exit_json(**result)

if __name__ == '__main__':
    main()