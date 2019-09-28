#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: lightsail_region_facts
short_description: Gather facts about AWS Lightsail regions.
description:
     - Gather facts about AWS Lightsail regions.
version_added: "2.5.3"
author: "Jack Ivanov (@jackivanov)"
options:
requirements:
  - "python >= 2.6"
  - boto3

extends_documentation_fragment:
  - aws
  - ec2
'''


EXAMPLES = '''
# Gather facts about all regions
- lightsail_region_facts:
'''

RETURN = '''
regions:
    returned: on success
    description: >
        Each element consists of a dict with all the information related
        to that region.
    type: list
    sample: "[{
                "availabilityZones": [],
                "continentCode": "NA",
                "description": "This region is recommended to serve users in the eastern United States",
                "displayName": "Virginia",
                "name": "us-east-1"
            }]"
'''

import time
import traceback

try:
    import botocore
    HAS_BOTOCORE = True
except ImportError:
    HAS_BOTOCORE = False

try:
    import boto3
except ImportError:
    # will be caught by imported HAS_BOTO3
    pass

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ec2 import (ec2_argument_spec, get_aws_connection_info, boto3_conn,
                                      HAS_BOTO3, camel_dict_to_snake_dict)

def main():
    argument_spec = ec2_argument_spec()
    module = AnsibleModule(argument_spec=argument_spec)

    if not HAS_BOTO3:
        module.fail_json(msg='Python module "boto3" is missing, please install it')

    if not HAS_BOTOCORE:
        module.fail_json(msg='Python module "botocore" is missing, please install it')

    try:
        region, ec2_url, aws_connect_kwargs = get_aws_connection_info(module, boto3=True)

        client = None
        try:
            client = boto3_conn(module, conn_type='client', resource='lightsail',
                                region=region, endpoint=ec2_url, **aws_connect_kwargs)
        except (botocore.exceptions.ClientError, botocore.exceptions.ValidationError) as e:
            module.fail_json(msg='Failed while connecting to the lightsail service: %s' % e, exception=traceback.format_exc())

        response = client.get_regions(
            includeAvailabilityZones=False
        )
        module.exit_json(changed=False, data=response)
    except (botocore.exceptions.ClientError, Exception) as e:
        module.fail_json(msg=str(e), exception=traceback.format_exc())


if __name__ == '__main__':
    main()
