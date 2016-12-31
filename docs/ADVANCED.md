# Advanced Usage

## Requirements

Before you begin, make sure you have installed all the dependencies necessary for your use case. Algo depends on the software below and most of it will be installed via the `requirements.txt` file.

* ansible >= 2.1
* python >= 2.6
* [dopy=0.3.5](https://github.com/Wiredcraft/dopy)
* [boto](https://github.com/boto/boto)
* [azure >= 0.7.1](https://github.com/Azure/azure-sdk-for-python)
* [apache-libcloud](https://github.com/apache/libcloud)
* [libcloud](https://curl.haxx.se/docs/caextract.html) (for Mac OS)
* [six](https://github.com/JioCloud/python-six) 
* SHell or BASH
* libselinux-python (for RedHat based distros)

## Local Deployment

**Warning**: If you run Algo on your existing server, the iptables rules will be overwritten. If you don't want to overwite the rules, just skip the `iptables` tag. You can find some information about tags below.

It is possible to download the Algo scripts to your own Ubuntu server and run the scripts locally. You need to install ansible to run Algo on Ubuntu. Installing ansible via pip requires pulling in a lot of dependencies, including a full compiler suite. It is easier to use apt, however, Ubuntu 16.04 only comes with ansible 2.0.0.2. Therefore, to use apt you must use the ansible PPA, and using a PPA requires installing `software-properties-common`.

tl;dr:

```
sudo apt-get install software-properties-common && sudo apt-add-repository ppa:ansible/ansible
sudo apt-get update && sudo apt-get install ansible
git clone https://github.com/trailofbits/algo
cd algo && ./algo
```

## Scripted Deployment

Example for DigitalOcean:

```
ansible-playbook deploy.yml -t digitalocean,vpn -e 'do_access_token=my_secret_token do_server_name=algo.local do_region=ams2'
```

### Roles

Cloud roles:
 
- role: cloud-digitalocean, tags: digitalocean
- role: cloud-ec2, tags: ec2
- role: cloud-gce, tags: gce

Server roles:

- role: vpn, tags: vpn 
- role: dns_adblocking, tags: dns, adblock
- role: proxy, tags: proxy, adblock
- role: logging, tags: logging
- role: security, tags: security
- role: ssh_tunneling, tags: ssh_tunneling

### Digital Ocean

Required variables:

- do_access_token
- do_server_name
- do_region

Possible regions:

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

### Google Cloud Engine

Required variables:

- credentials_file
- server_name
- ssh_public_key
- zone

Possible zones:

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

### Amazon EC2

Required variables:

- aws_access_key
- aws_secret_key
- aws_server_name
- ssh_public_key
- region

Possible regions:

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
- sa-east-1

### Local Installation

Required variables:

- server_ip
- server_user
- IP_subject_alt_name
