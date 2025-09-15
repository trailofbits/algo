# Deploying to Unsupported Cloud Providers

Algo officially supports the [cloud providers listed in the README](https://github.com/trailofbits/algo/blob/master/README.md#deploy-the-algo-server). If you want to deploy Algo on another cloud provider, that provider must meet specific technical requirements for compatibility.

## Technical Requirements

Your cloud provider must support:

1. **Ubuntu 22.04 LTS** - Algo exclusively supports Ubuntu 22.04 LTS as the base operating system
2. **Required kernel modules** - Specific modules needed for strongSwan IPsec and WireGuard VPN functionality
3. **Network capabilities** - Full networking stack access, not containerized environments

## Compatibility Testing

Before attempting to deploy Algo on an unsupported provider, test compatibility using strongSwan's kernel module checker:

1. Deploy a basic Ubuntu 22.04 LTS instance on your target provider
2. Run the [kernel module compatibility script](https://wiki.strongswan.org/projects/strongswan/wiki/KernelModules) from strongSwan
3. Verify all required modules are available and loadable

The script will identify any missing kernel modules that would prevent Algo from functioning properly.

## Adding Official Support

For Algo to officially support a new cloud provider, the provider must have:

- An available Ansible [cloud module](https://docs.ansible.com/ansible/list_of_cloud_modules.html)
- Reliable API for programmatic instance management
- Consistent Ubuntu 22.04 LTS image availability

If no Ansible module exists for your provider:

1. Check Ansible's [open issues](https://github.com/ansible/ansible/issues) and [pull requests](https://github.com/ansible/ansible/pulls) for existing development efforts
2. Consider developing the module yourself using the [Ansible module developer documentation](https://docs.ansible.com/ansible/dev_guide/developing_modules.html)
3. Reference your provider's API documentation for implementation details

## Unsupported Environments

### Container-Based Hosting

Providers using **OpenVZ**, **Docker containers**, or other **containerized environments** cannot run Algo because:

- Container environments don't provide access to kernel modules
- VPN functionality requires low-level network interface access
- IPsec and WireGuard need direct kernel interaction

For more details, see strongSwan's [Cloud Platforms documentation](https://wiki.strongswan.org/projects/strongswan/wiki/Cloudplatforms).

### Userland IPsec (libipsec)

Some providers attempt to work around kernel limitations using strongSwan's [kernel-libipsec](https://wiki.strongswan.org/projects/strongswan/wiki/Kernel-libipsec) plugin, which implements IPsec entirely in userspace.

**Algo does not support libipsec** for these reasons:

- **Performance issues** - Buffers each packet in memory, causing performance degradation
- **Resource consumption** - Can cause out-of-memory conditions on resource-constrained systems
- **Stability concerns** - May crash the charon daemon or lock up the host system
- **Security implications** - Less thoroughly audited than kernel implementations
- **Added complexity** - Introduces additional code paths that increase attack surface

We strongly recommend choosing a provider that supports native kernel modules rather than attempting workarounds.

## Alternative Deployment Options

If your preferred provider doesn't support Algo's requirements:

1. **Use a supported provider** - Deploy on AWS, DigitalOcean, Azure, GCP, or another [officially supported provider](https://github.com/trailofbits/algo/blob/master/README.md#deploy-the-algo-server)
2. **Deploy locally** - Use the [Ubuntu server deployment option](deploy-to-ubuntu.md) on your own hardware
3. **Hybrid approach** - Deploy the VPN server on a supported provider while using your preferred provider for other services

## Contributing Support

If you successfully deploy Algo on an unsupported provider and want to contribute official support:

1. Ensure the provider meets all technical requirements
2. Verify consistent deployment success across multiple regions
3. Create an Ansible module or verify existing module compatibility
4. Document the deployment process and any provider-specific considerations
5. Submit a pull request with your implementation

Community contributions to expand provider support are welcome, provided they meet Algo's security and reliability standards.
