# Advanced Usage

Make sure you have installed all the dependencies necessary for your operating system as described in the [README](../README.md).

## Local deployment

It is possible to download the Algo scripts to your own Ubuntu server and run the scripts locally. You need to install Ansible to run Algo on Ubuntu. Installing ansible via pip requires pulling in a lot of dependencies, including a full compiler suite. It would be easier to use apt, however, Ubuntu 16.04 only comes with Ansible 2.0.0.2. Therefore, to use apt you must use the ansible PPA, and using a PPA requires installing `software-properties-common`.

tl;dr:

```shell
sudo apt-get install software-properties-common && sudo apt-add-repository ppa:ansible/ansible
sudo apt-get update && sudo apt-get install ansible
git clone https://github.com/trailofbits/algo
cd algo && ./algo
```

**Warning**: If you run Algo on your existing server, the iptables rules will be overwritten. If you don't want to overwrite the rules, you must deploy via `ansible-playbook` and skip the `iptables` tag as described below.

## Scripted deployment

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
- role: proxy, tags: proxy, adblock
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

### Google Compute Engine

Required variables:

- credentials_file
- server_name
- ssh_public_key
- zone

Possible options for `zone`:

- us-central1-a
- us-central1-b
- us-central1-c
- us-central1-f
- us-east1-b
- us-east1-c
- us-east1-d
- europe-west1-b
- europe-west1-c
- europe-west1-d
- asia-east1-a
- asia-east1-b
- asia-east1-c
