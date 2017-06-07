# Scripted Deployment

Before you begin, make sure you have installed all the dependencies necessary for your operating system as described in the [README](../README.md).

You can deploy Algo non-interactively by running the Ansible playbooks directly with `ansible-playbook`.

`ansible-playbook` accepts "tags" via the `-t` or `TAGS` options. You can pass tags as a list of comma separated values. Ansible will only run plays (install roles) with the specified tags.

`ansible-playbook` accepts variables via the `-e` or `--extra-vars` option. You can pass variables as space separated key=value pairs. Algo requires certain variables that are listed below.

Here is a full example for DigitalOcean:

```shell
ansible-playbook deploy.yml -t digitalocean,vpn,cloud -e 'do_access_token=my_secret_token do_server_name=algo.local do_region=ams2'
```

### Ansible roles

Required tags:

- cloud

Cloud roles:

- role: cloud-digitalocean, tags: digitalocean
- role: cloud-ec2, tags: ec2
- role: cloud-gce, tags: gce

Server roles:

- role: vpn, tags: vpn
- role: dns_adblocking, tags: dns, adblock
- role: security, tags: security
- role: ssh_tunneling, tags: ssh_tunneling

Note: The `vpn` role generates Apple profiles with On-Demand Wifi and Cellular if you pass the following variables:

- OnDemandEnabled_WIFI=Y
- OnDemandEnabled_WIFI_EXCLUDE=HomeNet
- OnDemandEnabled_Cellular=Y

### Local Installation

Required tags:

- local

Required variables:

- server_ip
- server_user
- IP_subject_alt_name

Note that by default, the iptables rules on your existing server will be overwritten. If you don't want to overwrite the iptables rules, you can use the `--skip-tags iptables` flag, for example:

```shell
ansible-playbook deploy.yml -t local,vpn --skip-tags iptables -e 'server_ip=172.217.2.238 server_user=algo IP_subject_alt_name=172.217.2.238'
```

### Digital Ocean

Required variables:

- do_access_token
- do_server_name
- do_region

Possible options for `do_region`:

- ams2
- ams3
- fra1
- lon1
- nyc1
- nyc2
- nyc3
- sfo1
- sfo2
- sgp1
- tor1
- blr1

### Amazon EC2

Required variables:

- aws_access_key
- aws_secret_key
- aws_server_name
- ssh_public_key
- region

Possible options for `region`:

- us-east-1
- us-east-2
- us-west-1
- us-west-2
- ap-south-1
- ap-northeast-2
- ap-southeast-1
- ap-southeast-2
- ap-northeast-1
- eu-central-1
- eu-west-1
- eu-west-2

Additional tags:

- [encrypted](https://aws.amazon.com/blogs/aws/new-encrypted-ebs-boot-volumes/) (enabled by default)

#### Minimum required IAM permissions for deployment:

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
                "ec2:ImportKeyPair"
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
                "ec2:CreateInternetGateway",
                "ec2:DescribeVpcs",
                "ec2:CreateVpc",
                "ec2:DescribeInternetGateways",
                "ec2:ModifyVpcAttribute",
                "ec2:createTags",
                "ec2:CreateSubnet",
                "ec2:Associate*",
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

- credentials_file
- server_name
- ssh_public_key
- zone

Possible options for `zone`:

- us-west1-a
- us-west1-b
- us-west1-c
- us-central1-a
- us-central1-b
- us-central1-c
- us-central1-f
- us-east4-a
- us-east4-b
- us-east4-c
- us-east1-b
- us-east1-c
- us-east1-d
- europe-west1-b
- europe-west1-c
- europe-west1-d
- asia-southeast1-a
- asia-southeast1-b
- asia-east1-a
- asia-east1-b
- asia-east1-c
- asia-northeast1-a
- asia-northeast1-b
- asia-northeast1-c
