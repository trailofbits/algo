#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import traceback

from ansible.module_utils.basic import AnsibleModule, env_fallback, missing_required_lib
from ansible.module_utils.linode import get_user_agent

LINODE_IMP_ERR = None
try:
    from linode_api4 import StackScript, LinodeClient
    HAS_LINODE_DEPENDENCY = True
except ImportError:
    LINODE_IMP_ERR = traceback.format_exc()
    HAS_LINODE_DEPENDENCY = False


def create_stackscript(module, client, **kwargs):
    """Creates a stackscript and handles return format."""
    try:
        response = client.linode.stackscript_create(**kwargs)
        return response._raw_json
    except Exception as exception:
        module.fail_json(msg='Unable to query the Linode API. Saw: %s' % exception)


def stackscript_available(module, client):
    """Try to retrieve a stackscript."""
    try:
        label = module.params['label']
        desc = module.params['description']

        result = client.linode.stackscripts(StackScript.label == label,
                                            StackScript.description == desc,
                                            mine_only=True
                                          )
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
            script=dict(type='str', required=True),
            images=dict(type='list', required=True),
            description=dict(type='str', required=False),
            public=dict(type='bool', required=False, default=False),
        ),
        supports_check_mode=False
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
    stackscript = stackscript_available(module, client)

    if module.params['state'] == 'present' and stackscript is not None:
        module.exit_json(changed=False, stackscript=stackscript._raw_json)

    elif module.params['state'] == 'present' and stackscript is None:
        stackscript_json = create_stackscript(
            module, client,
            label=module.params['label'],
            script=module.params['script'],
            images=module.params['images'],
            desc=module.params['description'],
            public=module.params['public'],
        )
        module.exit_json(changed=True, stackscript=stackscript_json)

    elif module.params['state'] == 'absent' and stackscript is not None:
        stackscript.delete()
        module.exit_json(changed=True, stackscript=stackscript._raw_json)

    elif module.params['state'] == 'absent' and stackscript is None:
        module.exit_json(changed=False, stackscript={})


if __name__ == "__main__":
    main()
