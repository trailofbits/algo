# Deployment from Ansible

Before you begin, make sure you have installed all the dependencies necessary for your operating system as described in the [README](../README.md).

You can deploy Algo non-interactively by running the Ansible playbooks directly with `ansible-playbook`.

`ansible-playbook` accepts variables via the `-e` or `--extra-vars` option. You can pass variables as space separated key=value pairs. Algo requires certain variables that are listed below. You can also use the `--skip-tags` option to skip certain parts of the install, such as `iptables` (overwrite iptables rules), `ipsec` (install strongSwan), `wireguard` (install Wireguard). We don't recommend using the `-t` option as it will only include the tagged portions of the deployment, and skip certain necessary roles (such as `common`).

Here is a full example for DigitalOcean:

```shell
ansible-playbook main.yml -e "provider=digitalocean
                                server_name=algo
                                ondemand_cellular=false
                                ondemand_wifi=false
                                dns_adblocking=true
                                ssh_tunneling=true
                                store_pki=true
                                region=ams3
                                do_token=token"
```

See below for more information about variables and roles.

### Variables

- `provider` - (Required) The provider to use. See possible values below
- `server_name` - (Required) Server name. Default: algo
- `ondemand_cellular` (Optional) Enables VPN On Demand when connected to cellular networks for iOS/macOS clients using IPsec. Default: false
- `ondemand_wifi` - (Optional. See `ondemand_wifi_exclude`) Enables VPN On Demand when connected to WiFi networks for iOS/macOS clients using IPsec. Default: false
- `ondemand_wifi_exclude` (Required if `ondemand_wifi` set) - WiFi networks to exclude from using the VPN. Comma-separated values
- `dns_adblocking` - (Optional) Enables dnscrypt-proxy adblocking. Default: false
- `ssh_tunneling` - (Optional) Enable SSH tunneling for each user. Default: false
- `store_pki` - (Optional) Whether or not keep the CA key (required to add users in the future, but less secure). Default: false

If any of the above variables are unspecified, ansible will ask the user to input them.

### Ansible roles

Cloud roles can be activated by specifying an extra variable `provider`.

Cloud roles:

- role: cloud-digitalocean, [provider: digitalocean](#digital-ocean)
- role: cloud-ec2,          [provider: ec2](#amazon-ec2)
- role: cloud-gce,          [provider: gce](#google-compute-engine)
- role: cloud-vultr,        [provider: vultr](#vultr)
- role: cloud-azure,        [provider: azure](#azure)
- role: cloud-lightsail,    [provider: lightsail](#lightsail)
- role: cloud-scaleway,     [provider: scaleway](#scaleway)
- role: cloud-openstack,    [provider: openstack](#openstack)
- role: cloud-cloudstack,   [provider: cloudstack](#cloudstack)
- role: cloud-hetzner,      [provider: hetzner](#hetzner)
- role: cloud-linode,       [provider: linode](#linode)

Server roles:

- role: strongswan
  - Installs [strongSwan](https://www.strongswan.org/)
  - Enables AppArmor, limits CPU and memory access, and drops user privileges
  - Builds a Certificate Authority (CA) with [easy-rsa-ipsec](https://github.com/ValdikSS/easy-rsa-ipsec) and creates one client certificate per user
  - Bundles the appropriate certificates into Apple mobileconfig profiles for each user
- role: dns_adblocking
  - Installs DNS encryption through [dnscrypt-proxy](https://github.com/jedisct1/dnscrypt-proxy) with blacklists to be updated daily from `adblock_lists` in `config.cfg` - note this will occur even if `dns_encryption` in `config.cfg` is set to `false`
  - Constrains dnscrypt-proxy with AppArmor and cgroups CPU and memory limitations
- role: ssh_tunneling
  - Adds a restricted `algo` group with no shell access and limited SSH forwarding options
  - Creates one limited, local account and an SSH public key for each user
- role: wireguard
  - Installs a [Wireguard](https://www.wireguard.com/) server, with a startup script, and automatic checks for upgrades
  - Creates wireguard.conf files for Linux clients as well as QR codes for Apple/Android clients

Note: The `strongswan` role generates Apple profiles with On-Demand Wifi and Cellular if you pass the following variables:

- ondemand_wifi: true
- ondemand_wifi_exclude: HomeNet,OfficeWifi
- ondemand_cellular: true

### Local Installation

- role: local, provider: local

This role is intended to be run for local install onto an Ubuntu server, or onto an unsupported cloud provider's Ubuntu instance. Required variables:

- server - IP address of your server (or "localhost" if deploying to the local machine)
- endpoint - public IP address of the server you're installing on
- ssh_user - name of the SSH user you will use to install on the machine (passwordless login required). If `server=localhost`, this isn't required.
- ca_password - Password for the private CA key

Note that by default, the iptables rules on your existing server will be overwritten. If you don't want to overwrite the iptables rules, you can use the `--skip-tags iptables` flag.

### Digital Ocean

Required variables:

- do_token
- region

Possible options can be gathered calling to <https://api.digitalocean.com/v2/regions>

### Amazon EC2

Required variables:

- aws_access_key: `AKIA...`
- aws_secret_key
- region: e.g. `us-east-1`

Possible options can be gathered via cli `aws ec2 describe-regions`

Additional variables:

- [encrypted](https://aws.amazon.com/blogs/aws/new-encrypted-ebs-boot-volumes/) - Encrypted EBS boot volume. Boolean (Default: true)
- [size](https://aws.amazon.com/ec2/instance-types/) - EC2 instance type. String (Default: t2.micro)
- [image](https://awscli.amazonaws.com/v2/documentation/api/latest/reference/ec2/describe-images.html) - AMI `describe-images` search parameters to find the OS for the hosted image. Each OS and architecture has a unique AMI-ID. The OS owner, for example [Ubuntu](https://cloud-images.ubuntu.com/locator/ec2/), updates these images often. If parameters below result in multiple results, the most recent AMI-ID is chosen

   ```
   # Example of equivalent cli command
   aws ec2 describe-images --owners "099720109477" --filters "Name=architecture,Values=arm64" "Name=name,Values=ubuntu/images/hvm-ssd/ubuntu-jammy-22.04*"
   ```

  - [owners] - The operating system owner id. Default is [Canonical](https://help.ubuntu.com/community/EC2StartersGuide#Official_Ubuntu_Cloud_Guest_Amazon_Machine_Images_.28AMIs.29) (Default: 099720109477)
  - [arch] - The architecture (Default: x86_64, Optional: arm64)
  - [name] - The wildcard string to filter available ami names. Algo appends this name with the string "-\*64-server-\*", and prepends with "ubuntu/images/hvm-ssd/" (Default: Ubuntu latest LTS)
- [instance_market_type](https://aws.amazon.com/ec2/pricing/) - Two pricing models are supported: on-demand and spot. String (Default: on-demand)
  - If using spot instance types, one additional IAM permission along with the below minimum is required for deployment:

    ```
      "ec2:CreateLaunchTemplate"
    ```

#### Minimum required IAM permissions for deployment

```
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "PreDeployment",
            "Effect": "Allow",
            "Action": [
                "ec2:DescribeImages",
                "ec2:DescribeKeyPairs",
                "ec2:DescribeRegions",
                "ec2:ImportKeyPair",
                "ec2:CopyImage"
            ],
            "Resource": [
                "*"
            ]
        },
        {
            "Sid": "DeployCloudFormationStack",
            "Effect": "Allow",
            "Action": [
                "cloudformation:CreateStack",
                "cloudformation:UpdateStack",
                "cloudformation:DescribeStacks",
                "cloudformation:DescribeStackEvents",
                "cloudformation:ListStackResources"
            ],
            "Resource": [
                "*"
            ]
        },
        {
            "Sid": "CloudFormationEC2Access",
            "Effect": "Allow",
            "Action": [
                "ec2:DescribeRegions",
                "ec2:CreateInternetGateway",
                "ec2:DescribeVpcs",
                "ec2:CreateVpc",
                "ec2:DescribeInternetGateways",
                "ec2:ModifyVpcAttribute",
                "ec2:CreateTags",
                "ec2:CreateSubnet",
                "ec2:AssociateVpcCidrBlock",
                "ec2:AssociateSubnetCidrBlock",
                "ec2:AssociateRouteTable",
                "ec2:AssociateAddress",
                "ec2:CreateRouteTable",
                "ec2:AttachInternetGateway",
                "ec2:DescribeRouteTables",
                "ec2:DescribeSubnets",
                "ec2:ModifySubnetAttribute",
                "ec2:CreateRoute",
                "ec2:CreateSecurityGroup",
                "ec2:DescribeSecurityGroups",
                "ec2:AuthorizeSecurityGroupIngress",
                "ec2:RunInstances",
                "ec2:DescribeInstances",
                "ec2:AllocateAddress",
                "ec2:DescribeAddresses"
            ],
            "Resource": [
                "*"
            ]
        }
    ]
}
```

### Google Compute Engine

Required variables:

- gce_credentials_file: e.g. /configs/gce.json if you use the [GCE docs](https://trailofbits.github.io/algo/cloud-gce.html) - can also be defined in environment as GCE_CREDENTIALS_FILE_PATH
- [region](https://cloud.google.com/compute/docs/regions-zones/): e.g. `useast-1`

### Vultr

Required variables:

- [vultr_config](https://trailofbits.github.io/algo/cloud-vultr.html): /path/to/.vultr.ini
- [region](https://api.vultr.com/v1/regions/list): e.g. `Chicago`, `'New Jersey'`

### Azure

Required variables:

- azure_secret
- azure_tenant
- azure_client_id
- azure_subscription_id
- [region](https://azure.microsoft.com/en-us/global-infrastructure/regions/)

### Lightsail

Required variables:

- aws_access_key: `AKIA...`
- aws_secret_key
- region: e.g. `us-east-1`

Possible options can be gathered via cli `aws lightsail get-regions`

#### Minimum required IAM permissions for deployment

```
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "LightsailDeployment",
            "Effect": "Allow",
            "Action": [
                "lightsail:GetRegions",
                "lightsail:GetInstance",
                "lightsail:CreateInstances",
                "lightsail:DisableAddOn",
                "lightsail:PutInstancePublicPorts",
                "lightsail:StartInstance",
                "lightsail:TagResource",
                "lightsail:GetStaticIp",
                "lightsail:AllocateStaticIp",
                "lightsail:AttachStaticIp"
            ],
            "Resource": [
                "*"
            ]
        },
        {
            "Sid": "DeployCloudFormationStack",
            "Effect": "Allow",
            "Action": [
                "cloudformation:CreateStack",
                "cloudformation:UpdateStack",
                "cloudformation:DescribeStacks",
                "cloudformation:DescribeStackEvents",
                "cloudformation:ListStackResources"
            ],
            "Resource": [
                "*"
            ]
        }
    ]
}
```

### Scaleway

Required variables:

- [scaleway_token](https://www.scaleway.com/docs/generate-an-api-token/)
- region: e.g. `ams1`, `par1`

### OpenStack

You need to source the rc file prior to run Algo. Download it from the OpenStack dashboard->Compute->API Access and source it in the shell (eg: source /tmp/dhc-openrc.sh)

### CloudStack

Required variables:

- [cs_config](https://trailofbits.github.io/algo/cloud-cloudstack.html): /path/to/.cloudstack.ini
- cs_region: e.g. `exoscale`
- cs_zones: e.g. `ch-gva2`

The first two can also be defined in your environment, using the variables `CLOUDSTACK_CONFIG` and `CLOUDSTACK_REGION`.

### Hetzner

Required variables:

- hcloud_token: Your [API token](https://trailofbits.github.io/algo/cloud-hetzner.html#api-token) - can also be defined in the environment as HCLOUD_TOKEN
- region: e.g. `nbg1`

### Linode

Required variables:

- linode_token: Your [API token](https://trailofbits.github.io/algo/cloud-linode.html#api-token) - can also be defined in the environment as LINODE_TOKEN
- region: e.g. `us-east`

### Update users

Playbook:

```
users.yml
```

Required variables:

- server - IP or hostname to access the server via SSH
- ca_password - Password to access the CA key

Tags required:

- update-users
