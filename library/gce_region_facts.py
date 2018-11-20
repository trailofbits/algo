#!/usr/bin/python
# Copyright 2013 Google Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: gce_region_facts
version_added: "5.3"
short_description: Gather facts about GCE regions.
description:
    - Gather facts about GCE regions.
options:
  service_account_email:
    version_added: "1.6"
    description:
      - service account email
    required: false
    default: null
    aliases: []
  pem_file:
    version_added: "1.6"
    description:
      - path to the pem file associated with the service account email
        This option is deprecated. Use 'credentials_file'.
    required: false
    default: null
    aliases: []
  credentials_file:
    version_added: "2.1.0"
    description:
      - path to the JSON file associated with the service account email
    required: false
    default: null
    aliases: []
  project_id:
    version_added: "1.6"
    description:
      - your GCE project ID
    required: false
    default: null
    aliases: []
 requirements:
    - "python >= 2.6"
    - "apache-libcloud >= 0.13.3, >= 0.17.0 if using JSON credentials"
author: "Jack Ivanov (@jackivanov)"
'''

EXAMPLES = '''
# Gather facts about all regions
- gce_region_facts:
'''

RETURN = '''
regions:
    returned: on success
    description: >
        Each element consists of a dict with all the information related
        to that region.
    type: list
    sample: "[{
                "name": "asia-east1",
                "status": "UP",
                "zones": [
                    {
                        "name": "asia-east1-a",
                        "status": "UP"
                    },
                    {
                        "name": "asia-east1-b",
                        "status": "UP"
                    },
                    {
                        "name": "asia-east1-c",
                        "status": "UP"
                    }
                ]
            }]"
'''
try:
    from libcloud.compute.types import Provider
    from libcloud.compute.providers import get_driver
    from libcloud.common.google import GoogleBaseError, QuotaExceededError, ResourceExistsError, ResourceNotFoundError
    _ = Provider.GCE
    HAS_LIBCLOUD = True
except ImportError:
    HAS_LIBCLOUD = False

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.gce import gce_connect, unexpected_error_msg


def main():
    module = AnsibleModule(
        argument_spec=dict(
            service_account_email=dict(),
            pem_file=dict(type='path'),
            credentials_file=dict(type='path'),
            project_id=dict(),
        )
    )

    if not HAS_LIBCLOUD:
        module.fail_json(msg='libcloud with GCE support (0.17.0+) required for this module')

    gce = gce_connect(module)

    changed = False
    gce_regions = []

    try:
        regions = gce.ex_list_regions()
        for r in regions:
            gce_region = {}
            gce_region['name'] = r.name
            gce_region['status'] = r.status
            gce_region['zones'] = []
            for z in r.zones:
                gce_zone = {}
                gce_zone['name'] = z.name
                gce_zone['status'] = z.status
                gce_region['zones'].append(gce_zone)
            gce_regions.append(gce_region)
        json_output = { 'regions': gce_regions }
        module.exit_json(changed=False, results=json_output)
    except ResourceNotFoundError:
        pass


if __name__ == '__main__':
    main()
