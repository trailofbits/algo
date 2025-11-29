# Troubleshooting

First of all, check [this](https://github.com/trailofbits/algo#features) and ensure that you are deploying to Ubuntu 22.04 LTS, the only supported server platform.

  * [Installation Problems](#installation-problems)
     * General Setup
        * [Python version is not supported](#python-version-is-not-supported)
        * [Error: "ansible-playbook: command not found"](#error-ansible-playbook-command-not-found)
        * [Fatal: "Failed to validate the SSL certificate for ..."](#fatal-failed-to-validate-the-SSL-certificate)
        * [Bad owner or permissions on .ssh](#bad-owner-or-permissions-on-ssh)
     * Cloud Providers
        * [The region you want is not available](#the-region-you-want-is-not-available)
        * [AWS: SSH permission denied with an ECDSA key](#aws-ssh-permission-denied-with-an-ecdsa-key)
        * [AWS: "Deploy the template" fails with CREATE_FAILED](#aws-deploy-the-template-fails-with-create_failed)
        * [AWS: not authorized to perform: cloudformation:UpdateStack](#aws-not-authorized-to-perform-cloudformationupdatestack)
        * [Azure: No such file or directory .azure/azureProfile.json](#azure-no-such-file-or-directory-homeusernameazureazureprofilejson)
        * [Azure: Deployment Permissions Error](#azure-deployment-permissions-error)
        * [Linode: Stackscript error](#linode-error-unable-to-query-the-linode-api-saw-400-the-requested-distribution-is-not-supported-by-this-stackscript-)
     * Windows
        * [Windows: The value of parameter linuxConfiguration.ssh.publicKeys.keyData is invalid](#windows-the-value-of-parameter-linuxconfigurationsshpublickeyskeydata-is-invalid)
        * [Windows: "The parameter is incorrect" error when connecting](#windows-the-parameter-is-incorrect-error-when-connecting)
     * Local Deployment
        * [Error: Failed to create symlinks for deploying to localhost](#error-failed-to-create-symlinks-for-deploying-to-localhost)
        * [Wireguard: Unable to find 'configs/...' in expected paths](#wireguard-unable-to-find-configs-in-expected-paths)
     * Network
        * [Timeout when waiting for search string OpenSSH](#old-networking-firewall-in-place)
  * [Connection Problems](#connection-problems)
     * [I'm blocked or get CAPTCHAs when I access certain websites](#im-blocked-or-get-captchas-when-i-access-certain-websites)
     * [I want to change the list of trusted Wifi networks on my Apple device](#i-want-to-change-the-list-of-trusted-wifi-networks-on-my-apple-device)
     * [Error: "The VPN Service payload could not be installed."](#error-the-vpn-service-payload-could-not-be-installed)
     * [Little Snitch is broken when connected to the VPN](#little-snitch-is-broken-when-connected-to-the-vpn)
     * [I can't get my router to connect to the Algo server](#i-cant-get-my-router-to-connect-to-the-algo-server)
     * [Various websites appear to be offline through the VPN](#various-websites-appear-to-be-offline-through-the-vpn)
     * [Clients appear stuck in a reconnection loop](#clients-appear-stuck-in-a-reconnection-loop)
     * [Wireguard: clients can connect on Wifi but not LTE](#wireguard-clients-can-connect-on-wifi-but-not-lte)
     * [IPsec: Difficulty connecting through router](#ipsec-difficulty-connecting-through-router)
  * [Diagnostic Commands](#diagnostic-commands)
     * [Enable Verbose Logging](#enable-verbose-logging)
     * [Server-Side Diagnostics](#server-side-diagnostics)
     * [Client-Side Diagnostics](#client-side-diagnostics)
  * [I have a problem not covered here](#i-have-a-problem-not-covered-here)

## Installation Problems

Look here if you have a problem running the installer to set up a new Algo server.

### Python version is not supported

The minimum Python version required to run Algo is 3.11. Most modern operation systems should have it by default, but if the OS you are using doesn't meet the requirements, you have to upgrade. See the official documentation for your OS, or manual download it from https://www.python.org/downloads/. Otherwise, you may [deploy from docker](deploy-from-docker.md)

### Error: "ansible-playbook: command not found"

You tried to install Algo and you see an error that reads "ansible-playbook: command not found."

This indicates that Ansible is not installed or not available in your PATH. Algo automatically installs all dependencies (including Ansible) using uv when you run `./algo` for the first time. If you're seeing this error, try running `./algo` again - it should automatically install the required Python environment and dependencies. If the issue persists, ensure you're running `./algo` from the Algo project directory.

### Fatal: "Failed to validate the SSL certificate"

You received a message like this:
```
fatal: [localhost]: FAILED! => {"changed": false, "msg": "Failed to validate the SSL certificate for api.digitalocean.com:443. Make sure your managed systems have a valid CA certificate installed. You can use validate_certs=False if you do not need to confirm the servers identity but this is unsafe and not recommended. Paths checked for this platform: /etc/ssl/certs, /etc/ansible, /usr/local/etc/openssl. The exception msg was: [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get local issuer certificate (_ssl.c:1076).", "status": -1, "url": "https://api.digitalocean.com/v2/regions"}
```

Your local system does not have a CA certificate that can validate the cloud provider's API. This typically occurs with custom Python installations. Try reinstalling Python using Homebrew (`brew install python3`) or ensure your system has proper CA certificates installed.

### Bad owner or permissions on .ssh

You tried to run Algo and it quickly exits with an error about a bad owner or permissions:

```
fatal: [104.236.2.94]: UNREACHABLE! => {"changed": false, "msg": "Failed to connect to the host via ssh: Bad owner or permissions on /home/user/.ssh/config\r\n", "unreachable": true}
```

You need to reset the permissions on your `.ssh` directory. Run `chmod 700 /home/user/.ssh` and then `chmod 600 /home/user/.ssh/config`. You may need to repeat this for other files mentioned in the error message.

### The region you want is not available

Algo downloads the regions from the supported cloud providers (other than Microsoft Azure) listed in the first menu using APIs. If the region you want isn't available, the cloud provider has probably taken it offline for some reason. You should investigate further with your cloud provider.

If there's a specific region you want to install to in Microsoft Azure that isn't available, you should [file an issue](https://github.com/trailofbits/algo/issues/new), give us information about what region is missing, and we'll add it.

### AWS: SSH permission denied with an ECDSA key

You tried to deploy Algo to AWS and you received an error like this one:

```
TASK [Copy the algo ssh key to the local ssh directory] ************************
ok: [localhost -> localhost]

PLAY [Configure the server and install required software] **********************

TASK [Check the system] ********************************************************
fatal: [X.X.X.X]: UNREACHABLE! => {"changed": false, "msg": "Failed to connect to the host via ssh: Warning: Permanently added 'X.X.X.X' (ECDSA) to the list of known hosts.\r\nPermission denied (publickey).\r\n", "unreachable": true}
```

You previously deployed Algo to a hosting provider other than AWS, and Algo created an ECDSA keypair at that time. You are now deploying to AWS which [does not support ECDSA keys](https://aws.amazon.com/certificate-manager/faqs/) via their API. As a result, the deploy has failed.

In order to fix this issue, delete the `algo.pem` and `algo.pem.pub` keys from your `configs` directory and run the deploy again. If AWS is selected, Algo will now generate new RSA ssh keys which are compatible with the AWS API.

### AWS: "Deploy the template fails" with CREATE_FAILED

You tried to deploy Algo to AWS and you received an error like this one:

```
TASK [cloud-ec2 : Make a cloudformation template] ******************************
changed: [localhost]

TASK [cloud-ec2 : Deploy the template] *****************************************
fatal: [localhost]: FAILED! => {"changed": true, "events": ["StackEvent AWS::CloudFormation::Stack algopvpn1 ROLLBACK_COMPLETE", "StackEvent AWS::EC2::VPC VPC DELETE_COMPLETE", "StackEvent AWS::EC2::InternetGateway InternetGateway DELETE_COMPLETE", "StackEvent AWS::CloudFormation::Stack algopvpn1 ROLLBACK_IN_PROGRESS", "StackEvent AWS::EC2::VPC VPC CREATE_FAILED", "StackEvent AWS::EC2::VPC VPC CREATE_IN_PROGRESS", "StackEvent AWS::EC2::InternetGateway InternetGateway CREATE_FAILED", "StackEvent AWS::EC2::InternetGateway InternetGateway CREATE_IN_PROGRESS", "StackEvent AWS::CloudFormation::Stack algopvpn1 CREATE_IN_PROGRESS"], "failed": true, "output": "Problem with CREATE. Rollback complete", "stack_outputs": {}, "stack_resources": [{"last_updated_time": null, "logical_resource_id": "InternetGateway", "physical_resource_id": null, "resource_type": "AWS::EC2::InternetGateway", "status": "DELETE_COMPLETE", "status_reason": null}, {"last_updated_time": null, "logical_resource_id": "VPC", "physical_resource_id": null, "resource_type": "AWS::EC2::VPC", "status": "DELETE_COMPLETE", "status_reason": null}]}
```

Algo builds a [Cloudformation](https://aws.amazon.com/cloudformation/) template to deploy to AWS. You can find the entire contents of the Cloudformation template in `configs/algo.yml`. In order to troubleshoot this issue, login to the AWS console, go to the Cloudformation service, find the failed deployment, click the events tab, and find the corresponding "CREATE_FAILED" events. Note that all AWS resources created by Algo are tagged with `Environment => Algo` for easy identification.

In many cases, failed deployments are the result of [service limits](http://docs.aws.amazon.com/general/latest/gr/aws_service_limits.html) being reached, such as "CREATE_FAILED	AWS::EC2::VPC	VPC	The maximum number of VPCs has been reached." In these cases, you must either [delete the VPCs from previous deployments](https://docs.aws.amazon.com/AmazonVPC/latest/UserGuide/working-with-vpcs.html#VPC_Deleting), or [contact AWS support](https://console.aws.amazon.com/support/home?region=us-east-1#/case/create?issueType=service-limit-increase&limitType=service-code-direct-connect) to increase the limits on your account.

### AWS: not authorized to perform: cloudformation:UpdateStack

You tried to deploy Algo to AWS and you received an error like this one:

```
TASK [cloud-ec2 : Deploy the template] *****************************************
fatal: [localhost]: FAILED! => {"changed": false, "failed": true, "msg": "User: arn:aws:iam::082851645362:user/algo is not authorized to perform: cloudformation:UpdateStack on resource: arn:aws:cloudformation:us-east-1:082851645362:stack/algo/*"}
```

This error indicates you already have Algo deployed to Cloudformation. Need to [delete it](cloud-amazon-ec2.md#cleanup) first, then re-deploy.

### Azure: No such file or directory: '/home/username/.azure/azureProfile.json'

 ```
 TASK [cloud-azure : Create AlgoVPN Server] *****************************************************************************************************************************************************************
An exception occurred during task execution. To see the full traceback, use -vvv.
The error was: FileNotFoundError: [Errno 2] No such file or directory: '/home/ubuntu/.azure/azureProfile.json'
fatal: [localhost]: FAILED! => {"changed": false, "module_stderr": "Traceback (most recent call last):
File \"/usr/local/lib/python3.11/dist-packages/azure/cli/core/_session.py\", line 39, in load
with codecs_open(self.filename, 'r', encoding=self._encoding) as f:
File \"/usr/lib/python3.11/codecs.py\", line 897, in open\n    file = builtins.open(filename, mode, buffering)
FileNotFoundError: [Errno 2] No such file or directory: '/home/ubuntu/.azure/azureProfile.json'
", "module_stdout": "", "msg": "MODULE FAILURE
See stdout/stderr for the exact error", "rc": 1}
```

It happens when your machine is not authenticated in the azure cloud, follow this [guide](https://trailofbits.github.io/algo/cloud-azure.html) to configure your environment

### Azure: Deployment Permissions Error

The AAD Application Registration (aka, the 'Service Principal', where you got the ClientId) needs permission to create the resources for the subscription. Otherwise, you will get the following error when you run the Ansible deploy script:

```
fatal: [localhost]: FAILED! => {"changed": false, "msg": "Resource group create_or_update failed with status code: 403 and message: The client 'xxxxx' with object id 'THE_OBJECT_ID' does not have authorization to perform action 'Microsoft.Resources/subscriptions/resourcegroups/write' over scope '/subscriptions/THE_SUBSCRIPTION_ID/resourcegroups/algo' or the scope is invalid. If access was recently granted, please refresh your credentials."}
```

The solution for this is to open the Azure CLI and run the following command to grant contributor role to the Service Principal:

```
az role assignment create --assignee-object-id THE_OBJECT_ID --scope subscriptions/THE_SUBSCRIPTION_ID --role contributor
```

After this is applied, the Service Principal has permissions to create the resources and you can re-run `ansible-playbook main.yml` to complete the deployment.

### Linode Error: "Unable to query the Linode API. Saw: 400: The requested distribution is not supported by this stackscript.; "

StackScript is a custom deployment script that defines a set of configurations for a Linode instance (e.g. which distribution, specs, etc.). if you used algo with default values in the past deployments, a stackscript that would've been created is 're-used' in the deployment process (in fact, go see 'create Linodes' and under 'StackScripts' tab). Thus, there's a little chance that your deployment process will generate this 'unsupported stackscript' error due to a pre-existing StackScript that doesn't support a particular configuration setting or value due to an 'old' stackscript. The quickest solution is just to change the name of your deployment from the default value of 'algo' (or any other name that you've used before, again see the dashboard) and re-run the deployment.

### Windows: The value of parameter linuxConfiguration.ssh.publicKeys.keyData is invalid

You tried to deploy Algo from Windows and you received an error like this one:

```
TASK [cloud-azure : Create an instance].
fatal: [localhost]: FAILED! => {"changed": false,
"msg": "Error creating or updating virtual machine AlgoVPN - Azure Error:
InvalidParameter\n
Message: The value of parameter linuxConfiguration.ssh.publicKeys.keyData is invalid.\n
Target: linuxConfiguration.ssh.publicKeys.keyData"}
```

This is related to [the chmod issue](https://github.com/Microsoft/WSL/issues/81) inside /mnt directory which is NTFS. The fix is to place Algo outside of /mnt directory.

### Windows: "The parameter is incorrect" error when connecting

When trying to connect to your Algo VPN on Windows 10/11, you may receive an error stating "The parameter is incorrect". This is a common issue that can usually be resolved by resetting your Windows networking stack.

#### Solution

1. **Clear the networking caches**

   Open Command Prompt as Administrator (right-click on Command Prompt and select "Run as Administrator") and run these commands:
   ```cmd
   netsh int ip reset
   netsh int ipv6 reset
   netsh winsock reset
   ```

   Then restart your computer.

2. **Reset Device Manager network adapters** (if step 1 doesn't work)

   - Open Device Manager
   - Find "Network Adapters"
   - Uninstall all WAN Miniport drivers (IKEv2, IP, IPv6, etc.)
   - Click Action → Scan for hardware changes
   - The adapters you just uninstalled should reinstall automatically

   Try connecting to the VPN again.

#### What causes this issue?

This error typically occurs when:
- Windows networking stack becomes corrupted
- After Windows updates that affect network drivers
- When switching between different VPN configurations
- After network-related software installations/uninstallations

Note: This issue has been reported by many users and the above solution has proven effective in most cases.

### Error: Failed to create symlinks for deploying to localhost

You tried to run Algo and you received an error like this one:

```
TASK [Create a symlink if deploying to localhost] ********************************************************************
fatal: [localhost]: FAILED! => {"changed": false, "gid": 1000, "group": "ubuntu", "mode": "0775", "msg": "the directory configs/localhost is not empty, refusing to convert it", "owner": "ubuntu", "path": "configs/localhost", "size": 4096, "state": "directory", "uid": 1000}
included: /home/ubuntu/algo-master/playbooks/rescue.yml for localhost

TASK [debug] *********************************************************************************************************
ok: [localhost] => {
    "fail_hint": [
        "Sorry, but something went wrong!",
        "Please check the troubleshooting guide.",
        "https://trailofbits.github.io/algo/troubleshooting.html"
    ]
}

TASK [Fail the installation] *****************************************************************************************
```
This error is usually encountered when using the local install option and `localhost` is provided in answer to this question, which is expecting an IP address or domain name of your server:
```
Enter the public IP address or domain name of your server: (IMPORTANT! This is used to verify the certificate)
[localhost]
:
```

You should remove the files in /etc/wireguard/ and configs/ as follows:
```ssh
sudo rm -rf /etc/wireguard/*
rm -rf configs/*
```

And then immediately re-run `./algo` and provide a domain name or IP address in response to the question referenced above.

### Wireguard: Unable to find 'configs/...' in expected paths

You tried to run Algo and you received an error like this one:

```
TASK [wireguard : Generate public keys] ********************************************************************************
[WARNING]: Unable to find 'configs/xxx.xxx.xxx.xxx/wireguard//private/dan' in expected paths.

fatal: [localhost]: FAILED! => {"msg": "An unhandled exception occurred while running the lookup plugin 'file'. Error was a <class 'ansible.errors.AnsibleError'>, original message: could not locate file in lookup: configs/xxx.xxx.xxx.xxx/wireguard//private/dan"}
```
This error is usually hit when using the local install option on an unsupported server. Algo requires Ubuntu 22.04 LTS. You should upgrade your server to Ubuntu 22.04 LTS. If this doesn't work, try removing files in /etc/wireguard/ and the configs directories as follows:

```ssh
sudo rm -rf /etc/wireguard/*
rm -rf configs/*
```
Then immediately re-run `./algo`.

### Old Networking Firewall In Place

You may see the following output when attemptint to run ./algo from your localhost:

```
TASK [Wait until SSH becomes ready...] **********************************************************************************************************************
fatal: [localhost]: FAILED! => {"changed": false, "elapsed": 321, "msg": "Timeout when waiting for search string OpenSSH in xxx.xxx.xxx.xxx:4160"}
included: /home/<username>/algo/algo/playbooks/rescue.yml for localhost

TASK [debug] ************************************************************************************************************************************************
ok: [localhost] => {
    "fail_hint": [
        "Sorry, but something went wrong!",
        "Please check the troubleshooting guide.",
        "https://trailofbits.github.io/algo/troubleshooting.html"
    ]
}
```

If you see this error then one possible explanation is that you have a previous firewall configured in your cloud hosting provider which needs to be either updated or ideally removed. Removing this can often fix this issue.

## Connection Problems

Look here if you deployed an Algo server but now have a problem connecting to it with a client.

### I'm blocked or get CAPTCHAs when I access certain websites

This is normal.

When you deploy a Algo to a new cloud server, the address you are given may have been used before. In some cases, a malicious individual may have attacked others with that address and had it added to "IP reputation" feeds or simply a blacklist. In order to regain the trust for that address, you may be asked to enter CAPTCHAs to prove that you are a human, and not a Denial of Service (DoS) bot trying to attack others. This happens most frequently with Google. You can try entering the CAPTCHAs or you can try redeploying your Algo server to a new IP to resolve this issue.

In some cases, a website will block any visitors accessing their site through a cloud hosting provider due to previous, frequent DoS attacks originating from them. In these cases, there is not much you can do except deploy Algo to your own server or another IP that the website has not outright blocked.

### I want to change the list of trusted Wifi networks on my Apple device

This setting is enforced on your client device via the Apple profile you put on it. You can edit the profile with new settings, then load it on your device to change the settings. You can use the [Apple Configurator](https://itunes.apple.com/us/app/apple-configurator-2/id1037126344?mt=12) to edit and resave the profile. Advanced users can edit the file directly in a text editor. Use the [Configuration Profile Reference](https://developer.apple.com/library/content/featuredarticles/iPhoneConfigurationProfileRef/Introduction/Introduction.html) for information about the file format and other available options. If you're not comfortable editing the profile, you can also simply redeploy a new Algo server with different settings to receive a new auto-generated profile.

### Error: "The VPN Service payload could not be installed."

You tried to install the Apple profile on one of your devices and you received an error stating `The "VPN Service" payload could not be installed. The VPN service could not be created.` Client support for Algo VPN is limited to modern operating systems, e.g. macOS 10.11+, iOS 9+. Please upgrade your operating system and try again.

### Little Snitch is broken when connected to the VPN

Little Snitch is not compatible with IPSEC VPNs due to a known bug in macOS and there is no solution. The Little Snitch "filter" does not get incoming packets from IPSEC VPNs and, therefore, cannot evaluate any rules over them. Their developers have filed a bug report with Apple but there has been no response. There is nothing they or Algo can do to resolve this problem on their own. You can read more about this problem in [issue #134](https://github.com/trailofbits/algo/issues/134).

### I can't get my router to connect to the Algo server

In order to connect to the Algo VPN server, your router must support IKEv2, ECC certificate-based authentication, and the cipher suite we use. See the ipsec.conf files we generate in the `config` folder for more information. Note that we do not officially support routers as clients for Algo VPN at this time, though patches and documentation for them are welcome (for example, see open issues for [Ubiquiti](https://github.com/trailofbits/algo/issues/307) and [pfSense](https://github.com/trailofbits/algo/issues/292)).

### Various websites appear to be offline through the VPN

This issue appears occasionally due to issues with [MTU](https://en.wikipedia.org/wiki/Maximum_transmission_unit) size. Different networks may require the MTU to be within a specific range to correctly pass traffic. We made an effort to set the MTU to the most conservative, most compatible size by default but problems may still occur.

If either your Internet service provider or your chosen cloud service provider use an MTU smaller than the normal value of 1500 you can use the `reduce_mtu` option in the file `config.cfg` to correspondingly reduce the size of the VPN tunnels created by Algo. Algo will attempt to automatically set `reduce_mtu` based on the MTU found on the server at the time of deployment, but it cannot detect if the MTU is smaller on the client side of the connection.

If you change `reduce_mtu` you'll need to deploy a new Algo VPN.

To determine the value for `reduce_mtu` you should examine the MTU on your Algo VPN server's primary network interface (see below). You might algo want to run tests using `ping`, both on a local client *when not connected to the VPN* and also on your Algo VPN server (see below). Then take the smallest MTU you find (local or server side), subtract it from 1500, and use that for `reduce_mtu`. An exception to this is if you find the smallest MTU is your local MTU at 1492, typical for PPPoE connections, then no MTU reduction should be necessary.

#### Check the MTU on the Algo VPN server

To check the MTU on your server, SSH in to it, run the command `ifconfig`, and look for the MTU of the main network interface. For example:
```
ens4: flags=4163<UP,BROADCAST,RUNNING,MULTICAST>  mtu 1460
```
The MTU shown here is 1460 instead of 1500. Therefore set `reduce_mtu: 40` in `config.cfg`. Algo should do this automatically.

#### Determine the MTU using `ping`

When using `ping` you increase the payload size with the "Don't Fragment" option set until it fails. The largest payload size that works, plus the `ping` overhead of 28, is the MTU of the connection.

##### Example: Test on your Algo VPN server (Ubuntu)
```
$ ping -4 -s 1432 -c 1 -M do github.com
PING github.com (192.30.253.112) 1432(1460) bytes of data.
1440 bytes from lb-192-30-253-112-iad.github.com (192.30.253.112): icmp_seq=1 ttl=53 time=13.1 ms

--- github.com ping statistics ---
1 packets transmitted, 1 received, 0% packet loss, time 0ms
rtt min/avg/max/mdev = 13.135/13.135/13.135/0.000 ms

$ ping -4 -s 1433 -c 1 -M do github.com
PING github.com (192.30.253.113) 1433(1461) bytes of data.
ping: local error: Message too long, mtu=1460

--- github.com ping statistics ---
1 packets transmitted, 0 received, +1 errors, 100% packet loss, time 0ms
```
In this example the largest payload size that works is 1432. The `ping` overhead is 28 so the MTU is 1432 + 28 = 1460, which is 40 lower than the normal MTU of 1500. Therefore set `reduce_mtu: 40` in `config.cfg`.

##### Example: Test on a macOS client *not connected to your Algo VPN*
```
$ ping -c 1 -D -s 1464 github.com
PING github.com (192.30.253.113): 1464 data bytes
1472 bytes from 192.30.253.113: icmp_seq=0 ttl=50 time=169.606 ms

--- github.com ping statistics ---
1 packets transmitted, 1 packets received, 0.0% packet loss
round-trip min/avg/max/stddev = 169.606/169.606/169.606/0.000 ms

$ ping -c 1 -D -s 1465 github.com
PING github.com (192.30.253.113): 1465 data bytes

--- github.com ping statistics ---
1 packets transmitted, 0 packets received, 100.0% packet loss
```
In this example the largest payload size that works is 1464. The `ping` overhead is 28 so the MTU is 1464 + 28 = 1492, which is typical for a PPPoE Internet connection and does not require an MTU adjustment. Therefore use the default of `reduce_mtu: 0` in `config.cfg`.

#### Change the client MTU without redeploying the Algo VPN

If you don't wish to deploy a new Algo VPN (which is required to incorporate a change to `reduce_mtu`) you can change the client side MTU of WireGuard clients and Linux IPsec clients without needing to make changes to your Algo VPN.

For WireGuard on Linux, or macOS (when installed with `brew`), you can specify the MTU yourself in the client configuration file (typically `wg0.conf`). Refer to the documentation (see `man wg-quick`).

For WireGuard on iOS and Android you can change the MTU in the app.

For IPsec on Linux you can change the MTU of your network interface to match the required MTU. For example:
```
sudo ifconfig eth0 mtu 1440
```
To make the change take effect after a reboot, on Ubuntu 22.04 LTS edit the relevant file in the `/etc/netplan` directory (see `man netplan`).

#### Note for WireGuard iOS users

As of WireGuard for iOS 0.0.20190107 the default MTU is 1280, a conservative value intended to allow mobile devices to continue to work as they switch between different networks which might have smaller than normal MTUs. In order to use this default MTU review the configuration in the WireGuard app and remove any value for MTU that might have been added automatically by Algo.

### Clients appear stuck in a reconnection loop

If you're using 'Connect on Demand' on iOS and your client device appears stuck in a reconnection loop after switching from WiFi to LTE or vice versa, you may want to try disabling DoS protection in strongSwan.

The configuration value can be found in `/etc/strongswan.d/charon.conf`. After making the change you must reload or restart ipsec.

Example command:
```
sed -i -e 's/#*.dos_protection = yes/dos_protection = no/' /etc/strongswan.d/charon.conf && ipsec restart
```

### WireGuard: Clients can connect on Wifi but not LTE

Certain cloud providers (like AWS Lightsail) don't assign an IPv6 address to your server, but certain cellular carriers (e.g. T-Mobile in the United States, [EE](https://community.ee.co.uk/t5/4G-and-mobile-data/IPv4-VPN-Connectivity/td-p/757881) in the United Kingdom) operate an IPv6-only network. This somehow leads to the Wireguard app not being able to make a connection when transitioning to cell service. Go to the Wireguard app on the device when you're having problems with cell connectivity and select "Export log file" or similar option. If you see a long string of error messages like "`Failed to send data packet write udp6 [::]:49727->[2607:7700:0:2a:0:1:354:40ae]:51820: sendto: no route to host` then you might be having this problem.

Manually disconnecting and then reconnecting should restore your connection. To solve this, you need to either "force IPv4 connection" if available on your phone, or install an IPv4 APN, which might be available from your carrier tech support. T-mobile's is available [for iOS here under "iOS IPv4/IPv6 fix"](https://www.reddit.com/r/tmobile/wiki/index), and [here is a walkthrough for Android phones](https://www.myopenrouter.com/article/vpn-connections-not-working-t-mobile-heres-how-fix).

### IPsec: Difficulty connecting through router

Some routers treat IPsec connections specially because older versions of IPsec did not work properly through [NAT](https://en.wikipedia.org/wiki/Network_address_translation). If you're having problems connecting to your AlgoVPN through a specific router using IPsec you might need to change some settings on the router.

#### Change the "VPN Passthrough" settings

If your router has a setting called something like "VPN Passthrough" or "IPsec Passthrough" try changing the setting to a different value.

#### Change the default pfSense NAT rules

If your router runs [pfSense](https://www.pfsense.org) and a single IPsec client can connect but you have issues when using multiple clients, you'll need to change the **Outbound NAT** mode to **Manual Outbound NAT** and disable the rule that specifies **Static Port** for IKE (UDP port 500). See [Outbound NAT](https://docs.netgate.com/pfsense/en/latest/book/nat/outbound-nat.html#outbound-nat) in the [pfSense Book](https://docs.netgate.com/pfsense/en/latest/book).

## Diagnostic Commands

If you want to investigate issues yourself, here are useful commands to run on your Algo server.

### Enable Verbose Logging

By default, Algo minimizes logging for privacy. To enable detailed logging for debugging:

**During deployment** - Edit `config.cfg` before running `./algo`:
```yaml
algo_no_log: false              # Show detailed Ansible output (includes sensitive data!)
strongswan_log_level: 2         # IPsec debug logging (default: -1 disabled)
privacy_enhancements_enabled: false  # Disable log rotation/clearing
```

**Important:** Reset these to defaults before sharing logs or screenshots, as they may contain sensitive information.

### Server-Side Diagnostics

**Check service status:**
```bash
# WireGuard
systemctl status wg-quick@wg0
wg show                          # Show WireGuard interface and peers

# IPsec/StrongSwan
systemctl status strongswan
ipsec statusall                  # Show all IKE_SA and CHILD_SA
ipsec leases                     # Show assigned virtual IPs

# DNS
systemctl status dnscrypt-proxy.socket dnscrypt-proxy.service
ss -lnup | grep :53              # Check what's listening on DNS port
```

**View logs:**
```bash
# WireGuard (kernel module, limited logging)
dmesg | grep wireguard

# IPsec/StrongSwan
journalctl -u strongswan -f      # Follow strongswan logs
journalctl -t charon -f          # Follow IKE daemon logs

# DNS
journalctl -u dnscrypt-proxy -f

# General system
journalctl -f                    # Follow all system logs
```

**Check network and firewall:**
```bash
# Verify VPN interfaces exist
ip addr show wg0                 # WireGuard interface
ip addr show                     # All interfaces

# Check firewall rules
iptables -L -v -n                # IPv4 filter rules with counters
iptables -t nat -L -v -n         # IPv4 NAT rules
ip6tables -L -v -n               # IPv6 filter rules

# Test DNS resolution
dig @172.x.x.x google.com        # Replace with your local_service_ip
```

**Find your local DNS IP:**
```bash
grep local_service_ip /etc/dnsmasq.d/algo.conf 2>/dev/null || \
  grep listen_addresses /etc/dnscrypt-proxy/dnscrypt-proxy.toml
```

### Client-Side Diagnostics

**macOS:**
```bash
# View VPN-related logs (last hour)
log show --predicate 'subsystem == "com.apple.networkextension"' --info --last 1h

# Or use Console.app and search for: nesessionmanager
```

**Linux (WireGuard):**
```bash
sudo wg show
journalctl -t NetworkManager -f  # If using NetworkManager
```

**Windows:**
```powershell
# View VPN event logs
Get-WinEvent -LogName "Microsoft-Windows-VPN-Client/Operational" -MaxEvents 50
```

## I have a problem not covered here

If you have an issue that you cannot solve with the guidance here, please [file an issue](https://github.com/trailofbits/algo/issues/new). We welcome bug reports and want to hear about problems you encounter.
