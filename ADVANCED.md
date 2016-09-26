### Cloud Providers

**digitalocean**  
*Requirement variables:*  
- do_access_token  
- do_ssh_name  
- do_server_name  
- do_region

*Possible regions:*  
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

**gce**  
*Requirement variables:*  
- credentials_file
- server_name
- ssh_public_key
- zone

*Possible zones:*  
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

**ec2**  
*Requirement variables:*  
- aws_access_key
- aws_secret_key
- aws_server_name
- ssh_public_key
- region

*Possible regions:*  
- us-east-1
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

**local installation**  
*Requirement variables:*  
- server_ip
- server_user
- IP_subject_alt_name

### Deployment

Start the deploy with extra variables and tags that you need.  
Example for DigitalOcean:

```
ansible-playbook deploy.yml -t digitalocean,vpn -e 'do_access_token=secret_token_abc do_ssh_name=my_ssh_key do_server_name=algo.local do_region=ams2'
```

