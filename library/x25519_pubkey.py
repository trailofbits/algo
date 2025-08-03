#!/usr/bin/python

# x25519_pubkey.py - Ansible module to derive a base64-encoded WireGuard-compatible public key
# from a base64-encoded 32-byte X25519 private key.
#
# Why: community.crypto does not provide raw public key derivation for X25519 keys.

from ansible.module_utils.basic import AnsibleModule
from cryptography.hazmat.primitives.asymmetric import x25519
from cryptography.hazmat.primitives import serialization
import base64


def run_module():
    module_args = dict(
        private_key_b64=dict(type='str', required=False),
        private_key_path=dict(type='path', required=False),
        public_key_path=dict(type='path', required=False),
    )

    result = dict(
        changed=False,
        public_key='',
    )

    module = AnsibleModule(
        argument_spec=module_args,
        required_one_of=[['private_key_b64', 'private_key_path']],
        supports_check_mode=True
    )

    priv_b64 = None

    if module.params['private_key_path']:
        try:
            with open(module.params['private_key_path'], 'rb') as f:
                data = f.read().strip()
            try:
                # try decoding as base64 first
                base64.b64decode(data, validate=True)
                priv_b64 = data.decode()
            except Exception:
                # if not valid base64, assume raw 32 bytes and convert
                if len(data) != 32:
                    module.fail_json(msg=f"Private key file must be either base64 or exactly 32 raw bytes, got {len(data)}")
                priv_b64 = base64.b64encode(data).decode()
        except Exception as e:
            module.fail_json(msg=f"Failed to read private key file: {e}")
    else:
        priv_b64 = module.params['private_key_b64']

    try:
        priv_raw = base64.b64decode(priv_b64, validate=True)
    except Exception as e:
        module.fail_json(msg=f"Invalid base64 input: {e}")

    if len(priv_raw) != 32:
        module.fail_json(msg=f"Private key must decode to exactly 32 bytes, got {len(priv_raw)}")

    try:
        priv_key = x25519.X25519PrivateKey.from_private_bytes(priv_raw)
        pub_key = priv_key.public_key()
        pub_raw = pub_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )
        pub_b64 = base64.b64encode(pub_raw).decode()
        result['public_key'] = pub_b64

        if module.params['public_key_path']:
            pub_path = module.params['public_key_path']
            existing = None

            try:
                with open(pub_path, 'r') as f:
                    existing = f.read().strip()
            except FileNotFoundError:
                pass

            if existing != pub_b64:
                with open(pub_path, 'w') as f:
                    f.write(pub_b64)
                result['changed'] = True

            result['public_key_path'] = pub_path

    except Exception as e:
        module.fail_json(msg=f"Failed to derive public key: {e}")

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
