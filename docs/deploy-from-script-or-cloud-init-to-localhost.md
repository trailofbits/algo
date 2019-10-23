# Deploy from script or cloud-init

You can use `install.sh` to prepare the environment and deploy AlgoVPN on the local Ubuntu server in one shot using cloud-init, or run the script directly on the server after it's been created. 
The script doesn't configure any parameters in your cloud, so you're on your own to configure related [firewall rules](/docs/firewalls.md), a floating IP address and other resources you may need. The output of the install script (including the p12 and CA passwords) can be found at `/var/log/algo.log`, and user config files will be installed into the `/opt/algo/configs/localhost` directory. If you need to update users later, `cd /opt/algo`, change the user list in `config.cfg`, install additional dependencies as in step 4 of the [main README](https://github.com/trailofbits/algo/blob/master/README.md), and run `./algo update-users` from that directory.

## Cloud init deployment

You can copy-paste the snippet below to the user data (cloud-init or startup script) field when creating a new server. 

For now this has only been successfully tested on [DigitalOcean](https://www.digitalocean.com/docs/droplets/resources/metadata/), Amazon [EC2](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/user-data.html) and [Lightsail](https://lightsail.aws.amazon.com/ls/docs/en/articles/lightsail-how-to-configure-server-additional-data-shell-script), [Google Cloud](https://cloud.google.com/compute/docs/startupscript), [Azure](https://docs.microsoft.com/en-us/azure/virtual-machines/linux/using-cloud-init) and [Vultr](https://my.vultr.com/startup/), although Vultr doesn't [officially support cloud-init](https://www.vultr.com/docs/getting-started-with-cloud-init).

```
#!/bin/bash
curl -s https://raw.githubusercontent.com/trailofbits/algo/master/install.sh | sudo -E bash -x
```
The command will prepare the environment and install AlgoVPN with the default parameters below. If you want to modify the behavior you may define additional variables.

## Variables

- `METHOD`: which method of the deployment to use. Possible values are local and cloud. Default: cloud. The cloud method is intended to use in cloud-init deployments only. If you are not using cloud-init to deploy the server you have to use the local method.

- `ONDEMAND_CELLULAR`: "Connect On Demand" when connected to cellular networks. Boolean. Default: false.

- `ONDEMAND_WIFI`: "Connect On Demand" when connected to Wi-Fi. Default: false.

- `ONDEMAND_WIFI_EXCLUDE`: List the names of any trusted Wi-Fi networks where macOS/iOS IPsec clients should not use "Connect On Demand". Comma-separated list.

- `STORE_PKI`: To retain the PKI. (required to add users in the future, but less secure). Default: false.

- `DNS_ADBLOCKING`: To install an ad blocking DNS resolver. Default: false.

- `SSH_TUNNELING`: Enable SSH tunneling for each user. Default: false.

- `ENDPOINT`: The public IP address or domain name of your server: (IMPORTANT! This is used to verify the certificate). It will be gathered automatically for DigitalOcean, AWS, GCE, Azure or Vultr if the `METHOD` is cloud. Otherwise you need to define this variable according to your public IP address.

- `USERS`: list of VPN users. Comma-separated list. Default: user1.

- `REPO_SLUG`: Owner and repository that used to get the installation scripts from. Default: trailofbits/algo.

- `REPO_BRANCH`: Branch for `REPO_SLUG`. Default: master.

- `EXTRA_VARS`: Additional extra variables.

- `ANSIBLE_EXTRA_ARGS`: Any available ansible parameters. ie: `--skip-tags apparmor`.

## Examples

##### How to customise a cloud-init deployment by variables

```
#!/bin/bash
export ONDEMAND_CELLULAR=true
export SSH_TUNNELING=true
curl -s https://raw.githubusercontent.com/trailofbits/algo/master/install.sh | sudo -E bash -x
```

##### How to deploy locally without using cloud-init

```
export METHOD=local
export ONDEMAND_CELLULAR=true
export ENDPOINT=[your server's IP here]
curl -s https://raw.githubusercontent.com/trailofbits/algo/master/install.sh | sudo -E bash -x
```

##### How to deploy a server using arguments

The arguments order as per [variables](#variables) above

```
curl -s https://raw.githubusercontent.com/trailofbits/algo/master/install.sh | sudo -E bash -x -s local true false _null true true true true myvpnserver.com phone,laptop,desktop
```
