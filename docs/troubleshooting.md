# Troubleshooting

  * [Installation Problems](#installation-problems)
     * [Error: "You have not agreed to the Xcode license agreements"](#error-you-have-not-agreed-to-the-xcode-license-agreements)
     * [Error: checking whether the C compiler works... no](#error-checking-whether-the-c-compiler-works-no)
     * [Error: "fatal error: 'openssl/opensslv.h' file not found"](#error-fatal-error-opensslopensslvh-file-not-found)
     * [Error: "TypeError: must be str, not bytes"](#error-typeerror-must-be-str-not-bytes)
     * [Error: "ansible-playbook: command not found"](#error-ansible-playbook-command-not-found)
     * [Bad owner or permissions on .ssh](#bad-owner-or-permissions-on-ssh)
     * [The region you want is not available](#the-region-you-want-is-not-available)
	 * [AWS: SSH permission denied with an ECDSA key](#aws-ssh-permission-denied-with-an-ecdsa-key)
	 * [AWS: "Deploy the template" fails with CREATE_FAILED](#aws-deploy-the-template-fails-with-create_failed)
  * [Connection Problems](#connection-problems)
     * [I'm blocked or get CAPTCHAs when I access certain websites](#im-blocked-or-get-captchas-when-i-access-certain-websites)
     * [I want to change the list of trusted Wifi networks on my Apple device](#i-want-to-change-the-list-of-trusted-wifi-networks-on-my-apple-device)
     * [Error: "The VPN Service payload could not be installed."](#error-the-vpn-service-payload-could-not-be-installed)
     * [Little Snitch is broken when connected to the VPN](#little-snitch-is-broken-when-connected-to-the-vpn)
     * [I can't get my router to connect to the Algo server](#i-cant-get-my-router-to-connect-to-the-algo-server)
     * [I can't get Network Manager to connect to the Algo server](#i-cant-get-network-manager-to-connect-to-the-algo-server)
     * [Various websites appear to be offline through the VPN](#various-websites-appear-to-be-offline-through-the-vpn)
     * ["Error 809" or IKE_AUTH requests that never make it to the server](#error-809-or-ike_auth-requests-that-never-make-it-to-the-server)
  * [I have a problem not covered here](#i-have-a-problem-not-covered-here)

## Installation Problems

Look here if you have a problem running the installer to set up a new Algo server.

### Error: "You have not agreed to the Xcode license agreements"

On macOS, you tried to install the dependencies with pip and encountered the following error:

```
Downloading cffi-1.9.1.tar.gz (407kB): 407kB downloaded
  Running setup.py (path:/private/tmp/pip_build_root/cffi/setup.py) egg_info for package cffi

You have not agreed to the Xcode license agreements, please run 'xcodebuild -license' (for user-level acceptance) or 'sudo xcodebuild -license' (for system-wide acceptance) from within a Terminal window to review and agree to the Xcode license agreements.

    No working compiler found, or bogus compiler options
    passed to the compiler from Python's distutils module.
    See the error messages above.

----------------------------------------
Cleaning up...
Command python setup.py egg_info failed with error code 1 in /private/tmp/pip_build_root/cffi
Storing debug log for failure in /Users/algore/Library/Logs/pip.log
```

The Xcode compiler is installed but requires you to accept its license agreement prior to using it. Run `xcodebuild -license` to agree and then retry installing the dependencies.

### Error: checking whether the C compiler works... no

On macOS, you tried to install the dependencies with pip and encountered the following error:

```
Failed building wheel for pycrypto
Running setup.py clean for pycrypto
Failed to build pycrypto
...
copying lib/Crypto/Signature/PKCS1_v1_5.py -> build/lib.macosx-10.6-intel-2.7/Crypto/Signature
running build_ext
running build_configure
checking for gcc... gcc
checking whether the C compiler works... no
configure: error: in '/private/var/folders/3f/q33hl6_x6_nfyjg29fcl9qdr0000gp/T/pip-build-DB5VZp/pycrypto': configure: error: C compiler cannot create executables See config.log for more details
Traceback (most recent call last):
File "", line 1, in 
...
cmd_obj.run()
File "/private/var/folders/3f/q33hl6_x6_nfyjg29fcl9qdr0000gp/T/pip-build-DB5VZp/pycrypto/setup.py", line 278, in run
raise RuntimeError("autoconf error")
RuntimeError: autoconf error
```

You don't have a working compiler installed. You should install the XCode compiler by opening your terminal and running `xcode-select --install`.

### Error: "fatal error: 'openssl/opensslv.h' file not found"

On macOS, you tried to install pycrypto and encountered the following error:

```
build/temp.macosx-10.12-intel-2.7/_openssl.c:434:10: fatal error: 'openssl/opensslv.h' file not found

#include <openssl/opensslv.h>

        ^

1 error generated.

error: command 'cc' failed with exit status 1

----------------------------------------
Cleaning up...
Command /usr/bin/python -c "import setuptools, tokenize;__file__='/private/tmp/pip_build_root/cryptography/setup.py';exec(compile(getattr(tokenize, 'open', open)(__file__).read().replace('\r\n', '\n'), __file__, 'exec'))" install --record /tmp/pip-sREEE5-record/install-record.txt --single-version-externally-managed --compile failed with error code 1 in /private/tmp/pip_build_root/cryptography
Storing debug log for failure in /Users/algore/Library/Logs/pip.log
```

You are running an old version of `pip` that cannot build the `pycrypto` dependency. Upgrade to a new version of `pip` by running `sudo pip install -U pip`. 

### Error: "TypeError: must be str, not bytes"

You tried to install Algo and you see many repeated errors referencing `TypeError`, such as `TypeError: '>=' not supported between instances of 'TypeError' and 'int'` and `TypeError: must be str, not bytes`. For example:

```
TASK [Wait until SSH becomes ready...] *****************************************
An exception occurred during task execution. To see the full traceback, use -vvv. The error was: TypeError: must be str, not bytes
fatal: [localhost -> localhost]: FAILED! => {"changed": false, "failed": true, "module_stderr": "Traceback (most recent call last):\n  File \"/var/folders/x_/nvr61v455qq98vp22k5r5vm40000gn/T/ansible_6sdjysth/ansible_module_wait_for.py\", line 538, in <module>\n    main()\n  File \"/var/folders/x_/nvr61v455qq98vp22k5r5vm40000gn/T/ansible_6sdjysth/ansible_module_wait_for.py\", line 483, in main\n    data += response\nTypeError: must be str, not bytes\n", "module_stdout": "", "msg": "MODULE FAILURE"}
```

You may be trying to run Algo with Python3. Algo uses [Ansible](https://github.com/ansible/ansible) which has issues with Python3, although this situation is improving over time. Try running Algo with Python2 to fix this issue. Open your terminal and `cd` to the directory with Algo, then run: ``virtualenv -p `which python2.7` env && source env/bin/activate && pip install -r requirements.txt``

### Error: "ansible-playbook: command not found"

You tried to install Algo and you see an error that reads "ansible-playbook: command not found."

You did not finish step 4 in the installation instructions, "[Install Algo's remaining dependencies](https://github.com/trailofbits/algo#deploy-the-algo-server)." Algo depends on [Ansible](https://github.com/ansible/ansible), an automation framework, and this error indicates that you do not have Ansible installed. Ansible is installed by `pip` when you run `python -m pip install -r requirements.txt`. You must complete the installation instructions to run the Algo server deployment process.

### Bad owner or permissions on .ssh

You tried to run Algo and it quickly exits with an error about a bad owner or permissions:

```
fatal: [104.236.2.94]: UNREACHABLE! => {"changed": false, "msg": "Failed to connect to the host via ssh: Bad owner or permissions on /home/user/.ssh/config\r\n", "unreachable": true}
```

You need to reset the permissions on your `.ssh` directory. Run `chmod 700 /home/user/.ssh` and then `chmod 600 /home/user/.ssh/config`. You may need to repeat this for other files mentioned in the error message.

### The region you want is not available

You want to install Algo to a specific region in a cloud provider, but that region is not available in the list given by the installer. In that case, you should [file an issue](https://github.com/trailofbits/algo/issues/new). Cloud providers add new regions on a regular basis and we don't always keep up. File an issue and give us information about what region is missing and we'll add it.

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

You tried to deploy to Algo to AWS and you received an error like this one:

```
TASK [cloud-ec2 : Make a cloudformation template] ******************************
changed: [localhost]

TASK [cloud-ec2 : Deploy the template] *****************************************
fatal: [localhost]: FAILED! => {"changed": true, "events": ["StackEvent AWS::CloudFormation::Stack algopvpn1 ROLLBACK_COMPLETE", "StackEvent AWS::EC2::VPC VPC DELETE_COMPLETE", "StackEvent AWS::EC2::InternetGateway InternetGateway DELETE_COMPLETE", "StackEvent AWS::CloudFormation::Stack algopvpn1 ROLLBACK_IN_PROGRESS", "StackEvent AWS::EC2::VPC VPC CREATE_FAILED", "StackEvent AWS::EC2::VPC VPC CREATE_IN_PROGRESS", "StackEvent AWS::EC2::InternetGateway InternetGateway CREATE_FAILED", "StackEvent AWS::EC2::InternetGateway InternetGateway CREATE_IN_PROGRESS", "StackEvent AWS::CloudFormation::Stack algopvpn1 CREATE_IN_PROGRESS"], "failed": true, "output": "Problem with CREATE. Rollback complete", "stack_outputs": {}, "stack_resources": [{"last_updated_time": null, "logical_resource_id": "InternetGateway", "physical_resource_id": null, "resource_type": "AWS::EC2::InternetGateway", "status": "DELETE_COMPLETE", "status_reason": null}, {"last_updated_time": null, "logical_resource_id": "VPC", "physical_resource_id": null, "resource_type": "AWS::EC2::VPC", "status": "DELETE_COMPLETE", "status_reason": null}]}
```

Algo builds a [Cloudformation](https://aws.amazon.com/cloudformation/) template to deploy to AWS. You can find the entire contents of the Cloudformation template in `configs/algo.yml`. In order to troubleshoot this issue, login to the AWS console, go to the Cloudformation service, find the failed deployment, click the events tab, and find the corresponding "CREATE_FAILED" events. Note that all AWS resources created by Algo are tagged with `Environment => Algo` for easy identification.

In many cases, failed deployments are the result of [service limits](http://docs.aws.amazon.com/general/latest/gr/aws_service_limits.html) being reached, such as "CREATE_FAILED	AWS::EC2::VPC	VPC	The maximum number of VPCs has been reached." In these cases, you must [contact AWS support](https://console.aws.amazon.com/support/home?region=us-east-1#/case/create?issueType=service-limit-increase&limitType=service-code-direct-connect) to increase the limits on your account.

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

### I can't get Network Manager to connect to the Algo server

You're trying to connect Ubuntu or Debian to the Algo server through the Network Manager GUI but it's not working. Many versions of Ubuntu and some older versions of Debian bundle a [broken version of Network Manager](https://github.com/trailofbits/algo/issues/263) without support for modern standards or the strongSwan server. You must upgrade to Ubuntu 17.04 or Debian 9 Stretch, each of which contain the required minimum version of Network Manager.

### Various websites appear to be offline through the VPN

This issue appears intermittently due to issues with MTU size. If you experience this issue, we recommend [filing an issue](https://github.com/trailofbits/algo/issues/new) for assistance. Advanced users can troubleshoot the correct MTU size by retrying `ping` with the "don't fragment" bit set, then decreasing packet size until it works. This will determine the correct MTU size for your network, which you then need to update on your network adapter.

E.g., On Linux (client -- Ubuntu 16.04), connect to your IPsec tunnel then use the following commands to determine the correct MTU size:
```
$ ping -M do -s 1500 www.google.com
PING www.google.com (74.125.22.147) 1500(1528) bytes of data.
ping: local error: Message too long, mtu=1438
```
Then, set the MTU size on your network adapter (wlan0 or eth0):
```
$ sudo ifconfig wlan0 mtu 1438
```

### "Error 809" or IKE_AUTH requests that never make it to the server

On Windows, this issue may manifest with an error message that says "The network connection between your computer and the VPN server could not be established because the remote server is not responding... This is Error 809." On other operating systems, you may try to debug the issue by capturing packets with tcpdump and notice that, while IKE_SA_INIT request and responses are exchanged between the client and server, IKE_AUTH requests never make it to the server.

It is possible that the IKE_AUTH payload is too big to fit in a single IP datagram, and so is fragmented. Many consumer routers and cable modems ship with a feature that blocks "fragmented IP packets." Try logging into your router and disabling any firewall settings related to blocking or dropping fragmented IP packets. For more information, see [Issue #305](https://github.com/trailofbits/algo/issues/305).

## I have a problem not covered here

If you have an issue that you cannot solve with the guidance here, [join our Gitter](https://gitter.im/trailofbits/algo) and ask for help. If you think you found a new issue in Algo, [file an issue](https://github.com/trailofbits/algo/issues/new).
