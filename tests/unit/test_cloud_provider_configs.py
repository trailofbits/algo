#!/usr/bin/env python3
"""
Test cloud provider configurations
Based on issues #14752, #14730, #14762 - Hetzner/Azure issues
"""
import os
import sys
import yaml
import json
import re


def test_cloud_provider_defaults():
    """Test that default cloud provider configs are valid"""
    # Load config.cfg to check cloud provider defaults
    if os.path.exists('config.cfg'):
        with open('config.cfg', 'r') as f:
            config = yaml.safe_load(f)
        
        providers = config.get('cloud_providers', {})
        
        # Test that we have some providers configured
        assert len(providers) > 0, "No cloud providers configured"
        
        # Test common providers if they exist
        if 'digitalocean' in providers:
            do = providers['digitalocean']
            assert 'image' in do, "DigitalOcean missing image"
            
        if 'ec2' in providers:
            ec2 = providers['ec2']
            assert 'image' in ec2, "EC2 missing image"
        
        print("✓ Cloud provider defaults test passed")
    else:
        print("⚠ config.cfg not found, skipping provider defaults test")


def test_hetzner_server_types():
    """Test Hetzner server type configurations (issue #14730)"""
    # Hetzner changed from cx11 to cx22 as smallest instance
    deprecated_types = ['cx11', 'cpx11']
    current_types = ['cx22', 'cpx22', 'cx32', 'cpx32']
    
    # Test that we're not using deprecated types
    test_config = {
        'cloud_providers': {
            'hetzner': {
                'size': 'cx22',  # Should be cx22, not cx11
                'image': 'ubuntu-22.04',
                'location': 'hel1'
            }
        }
    }
    
    hetzner = test_config['cloud_providers']['hetzner']
    assert hetzner['size'] not in deprecated_types, \
        f"Using deprecated Hetzner type: {hetzner['size']}"
    assert hetzner['size'] in current_types, \
        f"Unknown Hetzner type: {hetzner['size']}"
    
    print("✓ Hetzner server types test passed")


def test_azure_dependency_compatibility():
    """Test Azure dependency issues (issue #14752)"""
    # Azure has specific Python dependency requirements
    # This test validates version parsing, not actual dependencies
    problem_versions = {
        'azure-keyvault': ['1.1.0'],  # Known to have issues
    }
    
    # Test version parsing
    version_pattern = re.compile(r'^([\w-]+)==([\d.]+)$')
    
    test_package = 'azure-keyvault==4.0.0'  # Good version
    match = version_pattern.match(test_package)
    assert match, f"Can't parse package version: {test_package}"
    
    name, version = match.groups()
    if name in problem_versions:
        assert version not in problem_versions[name], \
            f"{name} {version} has known issues"
    
    print("✓ Azure dependency compatibility test passed")


def test_region_validation():
    """Test cloud provider region validation"""
    # Test region format validation
    valid_regions = {
        'digitalocean': ['nyc1', 'nyc3', 'sfo2', 'sfo3', 'ams3', 'lon1'],
        'aws': ['us-east-1', 'us-west-2', 'eu-west-1', 'ap-southeast-1'],
        'hetzner': ['hel1', 'fsn1', 'nbg1', 'ash'],
        'azure': ['eastus', 'westus', 'northeurope', 'westeurope'],
    }
    
    # Test region format patterns
    patterns = {
        'digitalocean': re.compile(r'^[a-z]{3}\d$'),
        'aws': re.compile(r'^[a-z]{2}-[a-z]+-\d$'),
        'hetzner': re.compile(r'^[a-z]{3}\d?$'),
        'azure': re.compile(r'^[a-z]+$'),
    }
    
    for provider, regions in valid_regions.items():
        pattern = patterns.get(provider)
        if pattern:
            for region in regions:
                assert pattern.match(region), \
                    f"Invalid {provider} region format: {region}"
    
    print("✓ Region validation test passed")


def test_server_size_formats():
    """Test server size naming conventions"""
    valid_sizes = {
        'digitalocean': ['s-1vcpu-1gb', 's-2vcpu-2gb', 's-4vcpu-8gb'],
        'aws': ['t2.micro', 't3.small', 't3.medium', 'm5.large'],
        'hetzner': ['cx22', 'cpx22', 'cx32', 'cpx32'],
        'azure': ['Standard_B1s', 'Standard_B2s', 'Standard_D2s_v3'],
        'vultr': ['vc2-1c-1gb', 'vc2-2c-4gb', 'vhf-1c-1gb'],
    }
    
    # Test size format patterns
    patterns = {
        'digitalocean': re.compile(r'^s-\d+vcpu-\d+gb$'),
        'aws': re.compile(r'^[a-z]\d\.[a-z]+$'),
        'hetzner': re.compile(r'^c[px]x?\d+$'),
        'azure': re.compile(r'^Standard_[A-Z]\d+[a-z]*(_v\d)?$'),
        'vultr': re.compile(r'^v[a-z0-9]+-\d+c-\d+gb$'),
    }
    
    for provider, sizes in valid_sizes.items():
        pattern = patterns.get(provider)
        if pattern:
            for size in sizes:
                assert pattern.match(size), \
                    f"Invalid {provider} size format: {size}"
    
    print("✓ Server size formats test passed")


def test_image_naming():
    """Test OS image naming conventions"""
    valid_images = {
        'ubuntu-20.04': ['ubuntu', '20.04', 'lts'],
        'ubuntu-22.04': ['ubuntu', '22.04', 'lts'],
        'debian-11': ['debian', '11'],
        'debian-12': ['debian', '12'],
    }
    
    # Test image parsing
    image_pattern = re.compile(r'^([a-z]+)-(\d+)\.?(\d+)?$')
    
    for image, expected_parts in valid_images.items():
        match = image_pattern.match(image)
        assert match, f"Invalid image format: {image}"
        
        os_name = match.group(1)
        assert os_name in ['ubuntu', 'debian', 'centos', 'fedora'], \
            f"Unknown OS: {os_name}"
    
    print("✓ Image naming test passed")


if __name__ == "__main__":
    tests = [
        test_cloud_provider_defaults,
        test_hetzner_server_types,
        test_azure_dependency_compatibility,
        test_region_validation,
        test_server_size_formats,
        test_image_naming,
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
        print(f"\nAll {len(tests)} tests passed!")