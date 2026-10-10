# Oracle Cloud Infrastructure

Algo provisions an Oracle Cloud Infrastructure (OCI) VM and creates a dedicated VCN, public subnet, internet gateway, route table, and security list for it. The security list opens TCP SSH and UDP ports 500, 4500, and the configured WireGuard port. Outbound traffic is allowed for package installation and VPN traffic.

## Credentials

Create an API signing key and an OCI SDK config profile using the [OCI SDK configuration guide](https://docs.oracle.com/en-us/iaas/Content/API/Concepts/sdkconfig.htm). The default profile is `DEFAULT` in `~/.oci/config`. Keep the matching private key readable by the user running Algo.

Algo also accepts `OCI_CONFIG_FILE`, `OCI_CONFIG_PROFILE`, and `OCI_REGION`. You can pass `oci_config_file`, `oci_config_profile`, and `region` as Ansible variables instead. The deployment region defaults to the region in the selected profile.

## IAM permissions

Add a policy for the group that contains the API user. Replace the group and compartment names with values from your tenancy:

```text
Allow group InstanceLaunchers to manage instance-family in compartment <COMPARTMENT>
Allow group InstanceLaunchers to use volume-family in compartment <COMPARTMENT>
Allow group InstanceLaunchers to manage virtual-network-family in compartment <COMPARTMENT>
Allow group InstanceLaunchers to inspect availability-domains in tenancy
```

If you deploy into the tenancy root compartment, scope the first three statements to the root compartment. If you use a child compartment, pass its OCID with `oci_compartment_id` and scope those statements to that compartment.

## Deploy

Select **Oracle Cloud Infrastructure** in the provider menu or run:

```shell
./algo -e "provider=oracle"
```

The default shape is `VM.Standard.A1.Flex` with 2 OCPUs and 12 GB of memory, using Ampere's ARM processor. Oracle's current [Always Free allocation](https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm) allows up to 2 OCPUs and 12 GB across A1 instances in a tenancy. Availability depends on your account quota and region capacity. Algo finds the newest Ubuntu 22.04 image compatible with the selected shape and region; for A1 this is an ARM64 image. To use another shape, edit `cloud_providers.oracle.shape` in `config.cfg`; flexible shapes also need `cloud_providers.oracle.shape_config` set. See Oracle's [compute shape details](https://docs.oracle.com/en-us/iaas/Content/Compute/References/computeshapes.htm) for A1 limits.

The first deployment can take around 15 minutes while Ubuntu upgrades packages before SSH becomes available. Algo waits up to 20 minutes for Oracle's SSH port during this bootstrap.

Oracle's Ubuntu image has a guest firewall in addition to the VCN security list. During bootstrap, Algo opens the configured SSH port in the image's iptables rules and saves it for reboots. During VPN setup, Algo keeps the image's iptables backend and its `InstanceServices` rules, which protect access to Oracle's storage endpoints.

An instance created before this bootstrap fix can report `No route to host` for SSH even when the VCN security list allows the port. Changing cloud-init locally does not rerun it on an existing instance. Recreate a failed deployment to apply the updated bootstrap, or repair its guest firewall through a recovery shell. See [Oracle's explanation of Ubuntu firewall rules](https://blogs.oracle.com/developers/enabling-network-traffic-to-ubuntu-images-in-oracle-cloud-infrastructure) and [essential storage firewall rules](https://docs.oracle.com/en-us/iaas/Content/Compute/References/bestpracticescompute.htm).

Destroy the VM and the networking resources Algo created with:

```shell
./algo destroy <server-ip>
```

Deployment settings needed for destruction, including the selected config profile, compartment, and region, are saved with the server's local configuration.

## Related documentation

- [Oracle OCI Ansible collection](https://docs.oracle.com/en-us/iaas/tools/oci-ansible-collection/5.5.0/)
- [OCI SDK and CLI config file](https://docs.oracle.com/en-us/iaas/Content/API/Concepts/sdkconfig.htm)
- [Oracle IAM policy examples for launching instances](https://docs.oracle.com/en-us/iaas/Content/Identity/Concepts/commonpolicies.htm)
