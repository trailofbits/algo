#!/usr/bin/env python3
"""
Test that Ansible templates render correctly
This catches undefined variables, syntax errors, and logic bugs
"""
import os
import sys
import tempfile
from pathlib import Path

import yaml
from jinja2 import Environment, FileSystemLoader, StrictUndefined, UndefinedError, TemplateSyntaxError


# Mock Ansible filters that don't exist in plain Jinja2
def mock_to_uuid(value):
    """Mock the to_uuid filter"""
    return "12345678-1234-5678-1234-567812345678"


def mock_bool(value):
    """Mock the bool filter"""
    return str(value).lower() in ('true', '1', 'yes', 'on')


def mock_lookup(type, path):
    """Mock the lookup function"""
    # Return fake data for file lookups
    if type == 'file':
        if 'private' in path:
            return 'MOCK_PRIVATE_KEY_BASE64=='
        elif 'public' in path:
            return 'MOCK_PUBLIC_KEY_BASE64=='
        elif 'preshared' in path:
            return 'MOCK_PRESHARED_KEY_BASE64=='
    return 'MOCK_LOOKUP_DATA'


def get_test_variables():
    """Get a comprehensive set of test variables for template rendering"""
    return {
        # Server/Network basics
        'server_name': 'test-algo-vpn',
        'IP_subject_alt_name': '10.0.0.1',
        'ipv4_network_prefix': '10.19.49',
        'ipv4_network': '10.19.49.0',
        'ipv4_range': '10.19.49.2/24',
        'ipv6_network': 'fd9d:bc11:4020::/48',
        'ipv6_range': 'fd9d:bc11:4020::/64',
        'wireguard_enabled': True,
        'wireguard_port': 51820,
        'wireguard_PersistentKeepalive': 0,
        'wireguard_network': '10.19.49.0/24',
        'wireguard_network_ipv6': 'fd9d:bc11:4020::/48',
        
        # IPsec variables
        'ipsec_enabled': True,
        'strongswan_enabled': True,
        'strongswan_af': 'ipv4',
        'algo_ondemand_cellular': 'false',
        'algo_ondemand_wifi': 'false',
        'algo_ondemand_wifi_exclude': 'X251bGw=',
        'algo_ssh_tunneling': False,
        'algo_store_pki': True,
        
        # DNS
        'dns_adblocking': True,
        'algo_dns_adblocking': True,
        'adblock_lists': ['https://someblacklist.com'],
        'dns_encryption': True,
        'dns_servers': ['1.1.1.1', '1.0.0.1'],
        'local_dns': True,
        'alternative_ingress_ip': False,
        
        # Security/Firewall
        'snat_aipv4': False,
        'snat_aipv6': False,
        'block_smb': True,
        'block_netbios': True,
        
        # Users and auth
        'users': ['alice', 'bob', 'charlie'],
        'existing_users': ['alice'],
        'easyrsa_CA_password': 'test-ca-pass',
        'p12_export_password': 'test-export-pass',
        'CA_password': 'test-ca-pass',
        
        # System
        'ansible_ssh_port': 4160,
        'ansible_python_interpreter': '/usr/bin/python3',
        'BetweenClients_DROP': 'Y',
        'ssh_tunnels_config_path': '/etc/ssh/ssh_tunnels',
        'config_prefix': '/etc/algo',
        'server_user': 'algo',
        'IP': '10.0.0.1',
        
        # Missing variables found during testing
        'wireguard_pki_path': '/etc/wireguard/pki',
        'strongswan_log_level': '2',
        'wireguard_port_avoid': 53,
        'wireguard_port_actual': 51820,
        'reduce_mtu': 0,
        'ciphers': {
            'defaults': {
                'ike': 'aes128gcm16-prfsha512-ecp256,aes128-sha2_256-modp2048',
                'esp': 'aes128gcm16-ecp256,aes128-sha2_256-modp2048',
            },
            'ike': 'aes128gcm16-prfsha512-ecp256,aes128-sha2_256-modp2048',
            'esp': 'aes128gcm16-ecp256,aes128-sha2_256-modp2048',
        },
        
        # StrongSwan specific
        'strongswan_network': '10.19.48.0/24',
        'strongswan_network_ipv6': 'fd9d:bc11:4021::/64',
        'local_service_ip': '10.19.49.1',
        'local_service_ipv6': 'fd9d:bc11:4020::1',
        'ipv6_support': True,
        
        # WireGuard specific
        'wireguard_network_ipv4': '10.19.49.0/24',
        'wireguard_client_ip': '10.19.49.2/32,fd9d:bc11:4020::2/128',
        'wireguard_dns_servers': '1.1.1.1,1.0.0.1',
        
        # Cloud provider specific
        'algo_provider': 'local',
        'cloud_providers': ['ec2', 'gce', 'azure', 'do', 'lightsail', 'scaleway', 'openstack', 'cloudstack', 'hetzner', 'linode', 'vultr'],
        'provider_dns_servers': ['1.1.1.1', '1.0.0.1'],
        'ansible_ssh_private_key_file': '~/.ssh/id_rsa',
        
        # Defaults
        'inventory_hostname': 'localhost',
        'hostvars': {'localhost': {}},
        'groups': {'vpn-host': ['localhost']},
        'omit': 'OMIT_PLACEHOLDER',
    }


def find_templates():
    """Find all Jinja2 template files in the repo"""
    templates = []
    for pattern in ['**/*.j2', '**/*.jinja2', '**/*.yml.j2']:
        templates.extend(Path('.').glob(pattern))
    return templates


def test_template_syntax():
    """Test that all templates have valid Jinja2 syntax"""
    templates = find_templates()
    
    # Skip some paths that aren't real templates
    skip_paths = ['.git/', 'venv/', '.env/', 'configs/']
    
    # Skip templates that use Ansible-specific filters
    skip_templates = ['vpn-dict.j2', 'mobileconfig.j2', 'dnscrypt-proxy.toml.j2']
    
    errors = []
    skipped = 0
    for template_path in templates:
        # Skip unwanted paths
        if any(skip in str(template_path) for skip in skip_paths):
            continue
            
        # Skip templates with Ansible-specific features
        if any(skip in str(template_path) for skip in skip_templates):
            skipped += 1
            continue
            
        try:
            template_dir = template_path.parent
            env = Environment(
                loader=FileSystemLoader(template_dir),
                undefined=StrictUndefined
            )
            
            # Just try to load the template - this checks syntax
            template = env.get_template(template_path.name)
            
        except TemplateSyntaxError as e:
            errors.append(f"{template_path}: Syntax error - {e}")
        except Exception as e:
            errors.append(f"{template_path}: Error loading - {e}")
    
    if errors:
        print(f"✗ Template syntax check failed with {len(errors)} errors:")
        for error in errors[:10]:  # Show first 10 errors
            print(f"  - {error}")
        if len(errors) > 10:
            print(f"  ... and {len(errors) - 10} more")
        assert False, "Template syntax errors found"
    else:
        print(f"✓ Template syntax check passed ({len(templates) - skipped} templates, {skipped} skipped)")


def test_critical_templates():
    """Test that critical templates render with test data"""
    critical_templates = [
        'roles/wireguard/templates/client.conf.j2',
        'roles/strongswan/templates/ipsec.conf.j2',
        'roles/strongswan/templates/ipsec.secrets.j2',
        'roles/dns/templates/adblock.sh.j2',
        'roles/dns/templates/dnsmasq.conf.j2',
        'roles/common/templates/rules.v4.j2',
        'roles/common/templates/rules.v6.j2',
    ]
    
    test_vars = get_test_variables()
    errors = []
    
    for template_path in critical_templates:
        if not os.path.exists(template_path):
            continue  # Skip if template doesn't exist
            
        try:
            template_dir = os.path.dirname(template_path)
            template_name = os.path.basename(template_path)
            
            env = Environment(
                loader=FileSystemLoader(template_dir),
                undefined=StrictUndefined
            )
            
            # Add mock functions
            env.globals['lookup'] = mock_lookup
            env.filters['to_uuid'] = mock_to_uuid
            env.filters['bool'] = mock_bool
            
            template = env.get_template(template_name)
            
            # Add item context for templates that use loops
            if 'client' in template_name:
                test_vars['item'] = ('test-user', 'test-user')
            
            # Try to render
            output = template.render(**test_vars)
            
            # Basic validation - should produce some output
            assert len(output) > 0, f"Empty output from {template_path}"
            
        except UndefinedError as e:
            errors.append(f"{template_path}: Missing variable - {e}")
        except Exception as e:
            errors.append(f"{template_path}: Render error - {e}")
    
    if errors:
        print(f"✗ Critical template rendering failed:")
        for error in errors:
            print(f"  - {error}")
        assert False, "Critical template rendering errors"
    else:
        print("✓ Critical template rendering test passed")


def test_variable_consistency():
    """Check that commonly used variables are defined consistently"""
    # Variables that should be used consistently across templates
    common_vars = [
        'server_name',
        'IP_subject_alt_name',
        'wireguard_port',
        'wireguard_network',
        'dns_servers',
        'users',
    ]
    
    # Check if main.yml defines these
    if os.path.exists('main.yml'):
        with open('main.yml') as f:
            content = f.read()
            
        missing = []
        for var in common_vars:
            # Simple check - could be improved
            if var not in content:
                missing.append(var)
                
        if missing:
            print(f"⚠ Variables possibly not defined in main.yml: {missing}")
    
    print("✓ Variable consistency check completed")


def test_template_conditionals():
    """Test templates with different conditional states"""
    test_cases = [
        # WireGuard enabled, IPsec disabled
        {
            'wireguard_enabled': True,
            'ipsec_enabled': False,
            'dns_encryption': True,
            'dns_adblocking': True,
            'algo_ssh_tunneling': False,
        },
        # IPsec enabled, WireGuard disabled  
        {
            'wireguard_enabled': False,
            'ipsec_enabled': True,
            'dns_encryption': False,
            'dns_adblocking': False,
            'algo_ssh_tunneling': True,
        },
        # Both enabled
        {
            'wireguard_enabled': True,
            'ipsec_enabled': True,
            'dns_encryption': True,
            'dns_adblocking': True,
            'algo_ssh_tunneling': True,
        },
    ]
    
    base_vars = get_test_variables()
    
    for i, test_case in enumerate(test_cases):
        # Merge test case with base vars
        test_vars = {**base_vars, **test_case}
        
        # Test a few templates that have conditionals
        conditional_templates = [
            'roles/common/templates/rules.v4.j2',
        ]
        
        for template_path in conditional_templates:
            if not os.path.exists(template_path):
                continue
                
            try:
                template_dir = os.path.dirname(template_path)
                template_name = os.path.basename(template_path)
                
                env = Environment(
                    loader=FileSystemLoader(template_dir),
                    undefined=StrictUndefined
                )
                
                # Add mock functions
                env.globals['lookup'] = mock_lookup
                env.filters['to_uuid'] = mock_to_uuid
                env.filters['bool'] = mock_bool
                
                template = env.get_template(template_name)
                output = template.render(**test_vars)
                
                # Verify conditionals work
                if test_case.get('wireguard_enabled'):
                    assert str(test_vars['wireguard_port']) in output, \
                        f"WireGuard port missing when enabled (case {i})"
                        
            except Exception as e:
                print(f"✗ Conditional test failed for {template_path} case {i}: {e}")
                raise
    
    print("✓ Template conditional tests passed")


if __name__ == "__main__":
    # Check if we have Jinja2 available
    try:
        import jinja2
    except ImportError:
        print("⚠ Skipping template tests - jinja2 not installed")
        print("  Run: pip install jinja2")
        sys.exit(0)
    
    tests = [
        test_template_syntax,
        test_critical_templates,
        test_variable_consistency,
        test_template_conditionals,
    ]
    
    failed = 0
    for test in tests:
        try:
            test()
        except AssertionError as e:
            print(f"✗ {test.__name__} failed: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ {test.__name__} error: {e}")
            failed += 1
    
    if failed > 0:
        print(f"\n{failed} tests failed")
        sys.exit(1)
    else:
        print(f"\nAll {len(tests)} template tests passed!")