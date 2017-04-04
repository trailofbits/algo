## Table of Contents

1. [Error: "You have not agreed to the Xcode license agreements"](#1-error-you-have-not-agreed-to-the-xcode-license-agreements)
2. [Error: "fatal error: 'openssl/opensslv.h' file not found"](#2-error-fatal-error-opensslopensslvh-file-not-found)
3. [Error: "TypeError: must be str, not bytes"](#3-error-typeerror-must-be-str-not-bytes)
4. [Error: "ansible-playbook: command not found"](#4-error-ansible-playbook-command-not-found)
5. [Bad owner or permissions on .ssh](#5-bad-owner-or-permissions-on-ssh)
6. [Little Snitch is broken when connected to the VPN](#6-little-snitch-is-broken-when-connected-to-the-vpn)
7. [Various websites appear to be offline through the VPN](#7-various-websites-appear-to-be-offline-through-the-vpn)
8. [The region you want is not available](#8-the-region-you-want-is-not-available)
9. [I want to change the list of trusted Wifi networks on my Apple device](#9-i-want-to-change-the-list-of-trusted-wifi-networks-on-my-apple-device)
10. [Error: "The VPN Service payload could not be installed"](#10-error-the-vpn-service-payload-could-not-be-installed)
11. [I can't get my router to connect to the Algo server](#11-i-cant-get-my-router-to-connect-to-the-algo-server)
12. [I can't get Network Manager to connect to the Algo Server](#12-i-cant-get-network-manager-to-connect-to-the-algo-server)
13. [I have a problem not covered here](#i-have-a-problem-not-covered-here)

### 1. Error: "You have not agreed to the Xcode license agreements"

On macOS, you tried to install the dependencies with pip and encountered the following error:

```
Downloading cffi-1.9.1.tar.gz (407kB): 407kB downloaded
  Running setup.py (path:/private/tmp/pip_build_root/cffi/setup.py) egg_info for package cffi

You have not agreed to the Xcode license agreements, please run 'xcodebuild -license' (for user-level acceptance) or 'sudo xcodebuild -license' (for system-wide acceptance) from within a Terminal window to review and agree to the Xcode license agreements.

    No working compiler found, or bogus compiler options
    passed to the compiler from Python's distutils module.
    See the error messages above.
    (If they are about -mno-fused-madd and you are on OS/X 10.8,
    see http://stackoverflow.com/questions/22313407/ .)

----------------------------------------
Cleaning up...
Command python setup.py egg_info failed with error code 1 in /private/tmp/pip_build_root/cffi
Storing debug log for failure in /Users/algore/Library/Logs/pip.log
```

The Xcode compiler is installed but requires you to accept its license agreement prior to using it. Run `xcodebuild -license` to agree and then retry installing the dependencies.

### 2. Error: "fatal error: 'openssl/opensslv.h' file not found"

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

### 3. Error: "TypeError: must be str, not bytes"

You tried to install Algo and you see many repeated errors referencing `TypeError`, such as `TypeError: '>=' not supported between instances of 'TypeError' and 'int'` and `TypeError: must be str, not bytes`. For example:

```
TASK [Wait until SSH becomes ready...] *****************************************
An exception occurred during task execution. To see the full traceback, use -vvv. The error was: TypeError: must be str, not bytes
fatal: [localhost -> localhost]: FAILED! => {"changed": false, "failed": true, "module_stderr": "Traceback (most recent call last):\n  File \"/var/folders/x_/nvr61v455qq98vp22k5r5vm40000gn/T/ansible_6sdjysth/ansible_module_wait_for.py\", line 538, in <module>\n    main()\n  File \"/var/folders/x_/nvr61v455qq98vp22k5r5vm40000gn/T/ansible_6sdjysth/ansible_module_wait_for.py\", line 483, in main\n    data += response\nTypeError: must be str, not bytes\n", "module_stdout": "", "msg": "MODULE FAILURE"}
```

You may be trying to run Algo with Python3. Algo uses [Ansible](https://github.com/ansible/ansible) which has issues with Python3, although this situation is improving over time. Try running Algo with Python2 to fix this issue. Open your terminal and `cd` to the directory with Algo, then run: ``virtualenv -p `which python2.7` env && source env/bin/activate && pip install -r requirements.txt``

### 4. Error: "ansible-playbook: command not found"

You tried to install Algo and you see an error that reads "ansible-playbook: command not found."

You did not finish step 4 in the installation instructions, "[Install Algo's remaining dependencies](https://github.com/trailofbits/algo#deploy-the-algo-server)." Algo depends on [Ansible](https://github.com/ansible/ansible), an automation framework, and this error indicates that you do not have Ansible installed. Ansible is installed by `pip` when you run `python -m pip install -r requirements.txt`. You must complete the installation instructions to run the Algo server deployment process.

### 5. Bad owner or permissions on .ssh

You tried to run Algo and it quickly exits with an error about a bad owner or permissions:

```
fatal: [104.236.2.94]: UNREACHABLE! => {"changed": false, "msg": "Failed to connect to the host via ssh: Bad owner or permissions on /home/user/.ssh/config\r\n", "unreachable": true}
```

You need to reset the permissions on your `.ssh` directory. Run `chmod 700 /home/user/.ssh` and then `chmod 600 /home/user/.ssh/config`. You may need to repeat this for other files mentioned in the error message.

### 6. Little Snitch is broken when connected to the VPN

Little Snitch is not compatible with IPSEC VPNs due to a known bug in macOS and there is no solution. The Little Snitch "filter" does not get incoming packets from IPSEC VPNs and, therefore, cannot evaluate any rules over them. Their developers have filed a bug report with Apple but there has been no response. There is nothing they or Algo can do to resolve this problem on their own. You can read more about this problem in [issue #134](https://github.com/trailofbits/algo/issues/134).

### 7. Various websites appear to be offline through the VPN

This issue appears intermittently due to issues with MTU size. If you experience this issue, we recommend [filing an issue](https://github.com/trailofbits/algo/issues/new) for assistance. Advanced users can troubleshoot the correct MTU size by retrying `ping` with the "don't fragment" bit size and decreasing packet size. This will determine the correct MTU size for your network, which you then need to update on your network adapter.

### 8. The region you want is not available

You want to install Algo to a specific region in a cloud provider, but that region is not available in the list given by the installer. In that case, you should [file an issue](https://github.com/trailofbits/algo/issues/new). Cloud providers add new regions on a regular basis and we don't always keep up. File an issue and give us information about what region is missing and we'll add it.

### 9. I want to change the list of trusted Wifi networks on my Apple device

This setting is enforced on your client device via the Apple profile you put on it. You can edit the profile with new settings, then load it on your device to change the settings. You can use the [Apple Configurator](https://itunes.apple.com/us/app/apple-configurator-2/id1037126344?mt=12) to edit and resave the profile. Advanced users can edit the file directly in a text editor. Use the [Configuration Profile Reference](https://developer.apple.com/library/content/featuredarticles/iPhoneConfigurationProfileRef/Introduction/Introduction.html) for information about the file format and other available options. If you're not comfortable editing the profile, you can also simply redeploy a new Algo server with different settings to receive a new auto-generated profile.

### 10. Error: "The VPN Service payload could not be installed."

You tried to install the Apple profile on one of your devices and you received an error stating `The "VPN Service" payload could not be installed. The VPN service could not be created.` Client support for Algo VPN is limited to modern operating systems, e.g. macOS 10.11+, iOS 9+. Please upgrade your operating system and try again.

### 11. I can't get my router to connect to the Algo server

In order to connect to the Algo VPN server, your router must support IKEv2, ECC certificate-based authentication, and the cipher suite we use. See the ipsec.conf files we generate in the `config` folder for more information. Note that we do not officially support routers as clients for Algo VPN at this time, though patches and documentation for them are welcome (for example, see open issues for [Ubiquiti](https://github.com/trailofbits/algo/issues/307) and [pfSense](https://github.com/trailofbits/algo/issues/292)).

### 12. I can't get Network Manager to connect to the Algo server

You're trying to connect Ubuntu or Debian to the Algo server through the Network Manager GUI but it's not working. Many versions of Ubuntu and some older versions of Debian bundle a [broken version of Network Manager](https://github.com/trailofbits/algo/issues/263) without support for modern standards or the strongSwan server. You must upgrade to Ubuntu 17.04 or Debian 9 Stretch, each of which contain the required minimum version of Network Manager.

### I have a problem not covered here

If you have an issue that you cannot solve with the guidance here, [file an issue](https://github.com/trailofbits/algo/issues/new) that describes the problem and we'll do our best to help you. You can also [join our Slack](https://empireslacking.herokuapp.com/) and ask for help in the **#algo-support** channel.
