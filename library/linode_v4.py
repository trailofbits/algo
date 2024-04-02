#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import traceback

from ansible.module_utils.basic import AnsibleModule, env_fallback, missing_required_lib
from ansible.module_utils.linode import get_user_agent

LINODE_IMP_ERR = None
try:
    from linode_api4 import Instance, LinodeClient
    HAS_LINODE_DEPENDENCY = True
except ImportError:
    LINODE_IMP_ERR = traceback.format_exc()
    HAS_LINODE_DEPENDENCY = False


def create_linode(module, client, **kwargs):
    """Creates a Linode instance and handles return format."""
    if kwargs['root_pass'] is None:
        kwargs.pop('root_pass')

    try:
        response = client.linode.instance_create(**kwargs)
    except Exception as exception:
        module.fail_json(msg='Unable to query the Linode API. Saw: %s' % exception)

    try:
        if isinstance(response, tuple):
            instance, root_pass = response
            instance_json = instance._raw_json
            instance_json.update({'root_pass': root_pass})
            return instance_json
        else:
            return response._raw_json
    except TypeError:
        module.fail_json(msg='Unable to parse Linode instance creation'
                             ' response. Please raise a bug against this'
                             ' module on https://github.com/ansible/ansible/issues'
                         )


def maybe_instance_from_label(module, client):
    """Try to retrieve an instance based on a label."""
    try:
        label = module.params['label']
        result = client.linode.instances(Instance.label == label)
        return result[0]
    except IndexError:
        return None
    except Exception as exception:
        module.fail_json(msg='Unable to query the Linode API. Saw: %s' % exception)


def initialise_module():
    """Initialise the module parameter specification."""
    return AnsibleModule(
        argument_spec=dict(
            label=dict(type='str', required=True),
            state=dict(
                type='str',
                required=True,
                choices=['present', 'absent']
            ),
            access_token=dict(
                type='str',
                required=True,
                no_log=True,
                fallback=(env_fallback, ['LINODE_ACCESS_TOKEN']),
            ),
            authorized_keys=dict(type='list', required=False),
            group=dict(type='str', required=False),
            image=dict(type='str', required=False),
            region=dict(type='str', required=False),
            root_pass=dict(type='str', required=False, no_log=True),
            tags=dict(type='list', required=False),
            type=dict(type='str', required=False),
            stackscript_id=dict(type='int', required=False),
        ),
        supports_check_mode=False,
        required_one_of=(
            ['state', 'label'],
        ),
        required_together=(
            ['region', 'image', 'type'],
        )
    )


def build_client(module):
    """Build a LinodeClient."""
    return LinodeClient(
        module.params['access_token'],
        user_agent=get_user_agent('linode_v4_module')
    )


def main():
    """Module entrypoint."""
    module = initialise_module()

    if not HAS_LINODE_DEPENDENCY:
        module.fail_json(msg=missing_required_lib('linode-api4'), exception=LINODE_IMP_ERR)

    client = build_client(module)
    instance = maybe_instance_from_label(module, client)

    if module.params['state'] == 'present' and instance is not None:
        module.exit_json(changed=False, instance=instance._raw_json)

    elif module.params['state'] == 'present' and instance is None:
        instance_json = create_linode(
            module, client,
            authorized_keys=module.params['authorized_keys'],
            group=module.params['group'],
            image=module.params['image'],
            label=module.params['label'],
            region=module.params['region'],
            root_pass=module.params['root_pass'],
            tags=module.params['tags'],
            ltype=module.params['type'],
            stackscript_id=module.params['stackscript_id'],
        )
        module.exit_json(changed=True, instance=instance_json)

    elif module.params['state'] == 'absent' and instance is not None:
        instance.delete()
        module.exit_json(changed=True, instance=instance._raw_json)

    elif module.params['state'] == 'absent' and instance is None:
        module.exit_json(changed=False, instance={})


if __name__ == "__main__":
    main()
