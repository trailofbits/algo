# Amazon EC2 Cloud Setup

This guide walks you through setting up Algo VPN on Amazon EC2, including account creation, permissions configuration, and deployment process.

## AWS Account Creation

Creating an Amazon AWS account requires providing a phone number that can receive automated calls with PIN verification. The phone verification system occasionally fails, but you can request a new PIN and try again until it succeeds.

## Choose Your EC2 Plan

### AWS Free Tier

The most cost-effective option for new AWS customers is the [AWS Free Tier](https://aws.amazon.com/free/), which provides:

- 750 hours of Amazon EC2 Linux t2.micro or t3.micro instance usage per month
- 100 GB of outbound data transfer per month
- 30 GB of cloud storage

The Free Tier is available for 12 months from account creation. Some regions like Middle East (Bahrain), EU (Stockholm), and Israel (il-central-1) don't offer t2.micro instances, but t3.micro is available as an alternative.

Note that your Algo instance will continue working if you exceed bandwidth limits - you'll just start accruing standard charges on your AWS account.

### Cost-Effective Alternatives

If you're not eligible for the Free Tier or prefer more predictable costs, consider AWS Graviton instances. To use Graviton instances, modify your `config.cfg` file:

```yaml
ec2:
  size: t4g.nano
  arch: arm64
```

The t4g.nano instance is currently the least expensive option without promotional requirements. AWS is also running a promotion offering free t4g.small instances until December 31, 2025 - see the [AWS documentation](https://aws.amazon.com/ec2/faqs/#t4g-instances) for details.

For additional EC2 configuration options, see the [deploy from ansible guide](https://github.com/trailofbits/algo/blob/master/docs/deploy-from-ansible.md#amazon-ec2).

## Set Up IAM Permissions

### Create IAM Policy

1. In the AWS console, navigate to Services → IAM → Policies
2. Click "Create Policy"
3. Switch to the JSON tab
4. Replace the default content with the [minimum required AWS policy for Algo deployment](https://github.com/trailofbits/algo/blob/master/docs/deploy-from-ansible.md#minimum-required-iam-permissions-for-deployment)
5. Name the policy `AlgoVPN_Provisioning`

![Creating a new permissions policy in the AWS console.](/docs/images/aws-ec2-new-policy.png)

### Create IAM User

1. Navigate to Services → IAM → Users
2. Enable multi-factor authentication (MFA) on your root account using Google Authenticator or a hardware token
3. Click "Add User" and create a username (e.g., `algovpn`)
4. Select "Programmatic access"
5. Click "Next: Permissions"

![The new user screen in the AWS console.](/docs/images/aws-ec2-new-user.png)

6. Choose "Attach existing policies directly"
7. Search for "Algo" and select the `AlgoVPN_Provisioning` policy you created
8. Click "Next: Tags" (optional), then "Next: Review"

![Attaching a policy to an IAM user in the AWS console.](/docs/images/aws-ec2-attach-policy.png)

9. Review your settings and click "Create user"
10. Download the CSV file containing your access credentials - you'll need these for Algo deployment

![Downloading the credentials for an AWS IAM user.](/docs/images/aws-ec2-new-user-csv.png)

Keep the CSV file secure as it contains sensitive credentials that grant access to your AWS account.

## Deploy with Algo

Once you've installed Algo and its dependencies, you can deploy your VPN server to EC2.

### Provider Selection

Run `./algo` and select Amazon EC2 when prompted:

```
$ ./algo

  What provider would you like to use?
    1. DigitalOcean
    2. Amazon Lightsail
    3. Amazon EC2
    4. Microsoft Azure
    5. Google Compute Engine
    6. Hetzner Cloud
    7. Vultr
    8. Scaleway
    9. OpenStack (DreamCompute optimised)
    10. CloudStack
    11. Linode
    12. Install to existing Ubuntu server (for more advanced users)

Enter the number of your desired provider
: 3
```

### AWS Credentials

Algo will automatically detect AWS credentials in this order:

1. Command-line variables
2. Environment variables (`AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY`)
3. AWS credentials file (`~/.aws/credentials`)

If no credentials are found, you'll be prompted to enter them manually:

```
Enter your aws_access_key (http://docs.aws.amazon.com/general/latest/gr/managing-aws-access-keys.html)
Note: Make sure to use an IAM user with an acceptable policy attached (see https://github.com/trailofbits/algo/blob/master/docs/deploy-from-ansible.md).
[pasted values will not be displayed]
[AKIA...]:

Enter your aws_secret_key (http://docs.aws.amazon.com/general/latest/gr/managing-aws-access-keys.html)
[pasted values will not be displayed]
[ABCD...]:
```

For detailed credential configuration options, see the [AWS Credentials guide](aws-credentials.md).

### Server Configuration

You'll be prompted to name your server (default is "algo"):

```
Name the vpn server:
[algo]: algovpn
```

Next, select your preferred AWS region:

```
What region should the server be located in?
(https://docs.aws.amazon.com/general/latest/gr/rande.html#ec2_region)
    1. ap-northeast-1
    2. ap-northeast-2
    3. ap-south-1
    4. ap-southeast-1
    5. ap-southeast-2
    6. ca-central-1
    7. eu-central-1
    8. eu-north-1
    9. eu-west-1
    10. eu-west-2
    11. eu-west-3
    12. sa-east-1
    13. us-east-1
    14. us-east-2
    15. us-west-1
    16. us-west-2

Enter the number of your desired region
[13]
:
```

Choose a region close to your location for optimal performance, keeping in mind that some regions may have different pricing or instance availability.

After region selection, Algo will continue with the standard setup questions for user configuration and VPN options.

## Resource Cleanup

If you deploy Algo to EC2 multiple times, unused resources (instances, VPCs, subnets) may accumulate and potentially cause future deployment issues.

The cleanest way to remove an Algo deployment is through CloudFormation:

1. Go to the AWS console and navigate to CloudFormation
2. Find the stack associated with your Algo server
3. Delete the entire stack

Warning: Deleting a CloudFormation stack will permanently delete your EC2 instance and all associated resources unless you've enabled termination protection. Make sure you're deleting the correct stack and have backed up any important data.

This approach ensures all related AWS resources are properly cleaned up, preventing resource conflicts in future deployments.
