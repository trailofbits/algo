# Unsupported Cloud Providers

Algo officially supports the [cloud providers listed here](https://github.com/trailofbits/algo/blob/master/README.md#deploy-the-algo-server). If you want to deploy Algo on another virtual hosting provider, that provider must support:

1. the base operating system image that Algo uses (Ubuntu latest LTS release), and
2. a minimum of certain kernel modules required for the strongSwan IPsec server.

Please see the [Required Kernel Modules](https://wiki.strongswan.org/projects/strongswan/wiki/KernelModules) documentation from strongSwan for a list of the specific required modules and a script to check for them. As a first step, we recommend running their shell script to determine initial compatibility with your new hosting provider.

If you want Algo to officially support your new cloud provider then it must have an Ansible [cloud module](https://docs.ansible.com/ansible/list_of_cloud_modules.html) available. If no module is available for your provider, search Ansible's [open issues](https://github.com/ansible/ansible/issues) and [pull requests](https://github.com/ansible/ansible/pulls) for existing efforts to add it. If none are available, then you may want to develop the module yourself. Reference the [Ansible module developer documentation](https://docs.ansible.com/ansible/dev_guide/developing_modules.html) and the API documentation for your hosting provider.

## IPsec in userland

Hosting providers that rely on OpenVZ or Docker cannot be used by Algo since they cannot load the required kernel modules or access the required network interfaces. For more information, see the strongSwan documentation on [Cloud Platforms](https://wiki.strongswan.org/projects/strongswan/wiki/Cloudplatforms).

In order to address this issue, strongSwan has developed the [kernel-libipsec](https://wiki.strongswan.org/projects/strongswan/wiki/Kernel-libipsec) plugin which provides an IPsec backend that works entirely in userland. `libipsec` bundles its own IPsec implementation and uses TUN devices to route packets. For example, `libipsec` is used by the Android strongSwan app to address Android's lack of a functional IPsec stack.

Use of `libipsec` is not supported by Algo. It has known performance issues since it buffers each packet in memory. On certain systems with insufficient processor power, such as many cloud hosting providers, using `libipsec` can lead to an out of memory condition, crash the charon daemon, or lock up the entire host.

Further, `libipsec` introduces unknown security risks. The code in `libipsec` has not been scrutinized to the same level as the code in the Linux or FreeBSD kernel that it replaces. This additional code introduces new complexity to the Algo server that we want to avoid at this time. We recommend moving to a hosting provider that does not require libipsec and can load the required kernel modules.
