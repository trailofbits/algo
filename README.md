# Algo VPN

[![TravisCI Status](https://travis-ci.org/trailofbits/algo.svg?branch=master)](https://travis-ci.org/trailofbits/algo)
[![Slack Status](https://empireslacking.herokuapp.com/badge.svg)](https://empireslacking.herokuapp.com)
[![Twitter](https://img.shields.io/twitter/url/https/twitter.com/fold_left.svg?style=social&label=Follow%20%40AlgoVPN)](https://twitter.com/AlgoVPN)
[![Flattr](https://button.flattr.com/flattr-badge-large.png)](https://flattr.com/submit/auto?fid=kxw60j&url=https%3A%2F%2Fgithub.com%2Ftrailofbits%2Falgo)
[![PayPal](https://www.paypalobjects.com/en_US/i/btn/btn_donate_SM.gif)](https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=CYZZD39GXUJ3E)
[![Patreon](https://img.shields.io/badge/back_on-patreon-red.svg)](https://www.patreon.com/algovpn)

Algo VPN is a set of Ansible scripts that simplifies the setup of a personal IPSEC VPN. It contains the most secure defaults available, works with common cloud providers, and does not require client software on most devices.

## Features

* Supports only IKEv2 w/ a single cipher suite: AES-GCM, HMAC-SHA2, and P-256 DH
* Generates Apple Profiles to auto-configure iOS and macOS devices
* Provides helper scripts to add and remove users
* Blocks ads with a local DNS resolver and HTTP proxy (optional)
* Sets up limited SSH users for tunneling traffic (optional)
* Based on current versions of Ubuntu and strongSwan
* Installs to DigitalOcean, Amazon EC2, Google Compute Engine, Microsoft Azure, or your own server

## Anti-features

* Does not support legacy cipher suites or protocols like L2TP, IKEv1, or RSA
* Does not install Tor, OpenVPN, or other risky servers
* Does not depend on the security of [TLS](https://tools.ietf.org/html/rfc7457)
* Does not require client software on most platforms
* Does not claim to provide anonymity or censorship avoidance
* Does not claim to protect you from the [FSB](https://en.wikipedia.org/wiki/Federal_Security_Service), [MSS](https://en.wikipedia.org/wiki/Ministry_of_State_Security_(China)), [DGSE](https://en.wikipedia.org/wiki/Directorate-General_for_External_Security), or [FSM](https://en.wikipedia.org/wiki/Flying_Spaghetti_Monster)

## Deploy the Algo Server

The easiest way to get an Algo server running is to let it set up a _new_ virtual machine in the cloud for you.

1. **Setup an account on a cloud hosting provider.** Algo supports [DigitalOcean](https://www.digitalocean.com/) (most user friendly), [Amazon EC2](https://aws.amazon.com/), [Google Compute Engine](https://cloud.google.com/compute/), and [Microsoft Azure](https://azure.microsoft.com/).

2. [Download Algo](https://github.com/trailofbits/algo/archive/master.zip) and decompress it in a convenient location on your local machine.

3. Install Algo's core dependencies. Open the Terminal. The `python` interpreter you use to deploy Algo must be python2. If you don't know what this means, you're probably fine. `cd` into the directory where you downloaded Algo, then run:
    
    - macOS:
      ```bash
      $ python -m ensurepip --user
      $ python -m pip install --user --upgrade virtualenv
      ```
    - Linux (deb-based): 
      ```bash
      $ sudo apt-get update && sudo apt-get install \
          build-essential \
          libssl-dev \
          libffi-dev \
          python-dev \
          python-pip \
          python-setuptools \
          python-virtualenv -y
      ```
     - Linux (rpm-based): See the [Pre-Install Documentation for RedHat/CentOS 6.x](docs/pre-install_redhat_centos_6.x.md)
     - Windows: See the [Windows documentation](docs/WINDOWS.md)

4. Install Algo's remaining dependencies for your operating system. Using the same terminal window as the previous step run the command below.
    ```bash
    $ python -m virtualenv env && source env/bin/activate && python -m pip install -r requirements.txt 
    ```
    On macOS, you may be prompted to install `cc` which you should accept.

5. Open `config.cfg` in your favorite text editor. Specify the users you wish to create in the `users` list.

6. Start the deployment. Return to your terminal. In the Algo directory, run `./algo` and follow the instructions. There are several optional features available. None are required for a fully functional VPN server. These optional features are described in greater detail in [ROLES.md](docs/ROLES.md).

That's it! You will get the message below when the server deployment process completes. You now have an Algo server on the internet. Take note of the p12 (user certificate) password in case you need it later.

You can now setup clients to connect it, e.g. your iPhone or laptop. Proceed to [Configure the VPN Clients](https://github.com/trailofbits/algo#configure-the-vpn-clients) below.

```
        "\"#----------------------------------------------------------------------#\"",
        "\"#                          Congratulations!                            #\"",
        "\"#                     Your Algo server is running.                     #\"",
        "\"#    Config files and certificates are in the ./configs/ directory.    #\"",
        "\"#              Go to https://whoer.net/ after connecting               #\"",
        "\"#        and ensure that all your traffic passes through the VPN.      #\"",
        "\"#          Local DNS resolver and Proxy IP address: 172.16.0.1         #\"",
        "\"#                The p12 and SSH keys password is XXXXXXXX             #\"",
        "\"#----------------------------------------------------------------------#\"",
```

Note: If you want to run Algo again at any point in the future, you must first "reactivate" the dependencies for it. To reactivate them, open your terminal, use `cd` to navigate to the directory with Algo, then run `source env/bin/activate`.

Advanced users who want to install Algo on top of a server they already own or want to script the deployment of Algo onto a network of servers, please see the [Advanced Usage](/docs/ADVANCED.md) documentation.

## Configure the VPN Clients

Certificates and configuration files that users will need are placed in the `configs` directory. Make sure to secure these files since many contain private keys. All files are prefixed with the IP address of your new Algo VPN server.

### Apple Devices

Find the corresponding mobileconfig (Apple Profile) for each user and send it to them over AirDrop or other secure means. Apple Configuration Profiles are all-in-one configuration files for iOS and macOS devices. On macOS, double-clicking a profile to install it will fully configure the VPN. On iOS, users are prompted to install the profile as soon as the AirDrop is accepted.

### Android Devices

You need to install the [StrongSwan VPN Client for Android 4 and newer](https://play.google.com/store/apps/details?id=org.strongswan.android) because no version of Android supports IKEv2. Import the corresponding user.p12 certificate to your device. See the [Android setup instructions](/docs/ANDROID.md) for more detailed steps.

### Windows

Copy the CA certificate, user certificate, and the user PowerShell script to the client computer. Import the CA certificate to the local machine Trusted Root certificate store. Then, run the included PowerShell script to import the user certificate, set up a VPN connection, and activate stronger ciphers on it.

If you want to perform these steps by hand, you will need to import the user certificate to the Personal certificate store, add an IKEv2 connection in the network settings, then activate stronger ciphers on it via the following PowerShell script:

`Set-VpnConnectionIPsecConfiguration -ConnectionName "Algo" -AuthenticationTransformConstants SHA25612
8 -CipherTransformConstants AES256 -EncryptionMethod AES256 -IntegrityCheckMethod SHA256 -DHGroup Group14 -PfsGroup none`

### Linux strongSwan Clients (e.g., OpenWRT, Ubuntu, etc.)

Install strongSwan, then copy the included user_ipsec.conf, user_ipsec.secrets, user.crt (user certificate), and user.key (private key) files to your client device. These may require some customization based on your exact use case. These files were originally generated with a point-to-point OpenWRT-based VPN in mind.

### Other Devices

Depending on the platform, you may need one or multiple of the following files.

* ca.crt: CA Certificate
* user_ipsec.conf: StrongSwan client configuration
* user_ipsec.secrets: StrongSwan client configuration
* user.crt: User Certificate
* user.key: User Private Key
* user.mobileconfig: Apple Profile
* user.p12: User Certificate and Private Key (in PKCS#12 format)
* user_windows.ps1: Powershell script to setup a VPN connection on Windows

## Setup an SSH Tunnel

If you turned on the optional SSH tunneling role, then local user accounts will be created for each user in `config.cfg` and an SSH authorized_key files for them will be in the `configs` directory (user.ssh.pem). SSH user accounts do not have shell access, cannot authenticate with a password, and only have limited tunneling options (e.g., `ssh -N` is required). This is done to ensure that SSH users have the least access required to tunnel through the server and can perform no other actions.

Use the example command below to start an SSH tunnel by replacing `user` and `ip` with your own. Once the tunnel is setup, you can configure a browser or other application to use 127.0.0.1:1080 as a SOCKS proxy to route traffic through the Algo server.

 `ssh -D 127.0.0.1:1080 -f -q -C -N user@ip -i configs/ip_user.ssh.pem`

## Adding or Removing Users

Algo's own scripts can easily add and remove users from the VPN server.

1. Update the `users` list in your `config.cfg`
2. Open a terminal, `cd` to the algo directory, and activate the virtual environment with `source env/bin/activate`
3. Run the command: `./algo update-users`

The Algo VPN server now contains only the users listed in the `config.cfg` file.

## Additional Documentation

* [Advanced Usage](docs/ADVANCED.md) describes how to deploy an Algo VPN server directly from Ansible.
* [FAQ](docs/FAQ.md) includes answers to common questions.
* [Roles](docs/ROLES.md) includes a description of optional Algo VPN server features.
* [Troubleshooting](docs/TROUBLESHOOTING.md) includes answers to common technical issues.

## Endorsements

> I've been ranting about the sorry state of VPN svcs for so long, probably about
> time to give a proper talk on the subject. TL;DR: use Algo.

-- [Kenn White](https://twitter.com/kennwhite/status/814166603587788800)

> Before picking a VPN provider/app, make sure you do some research
> https://research.csiro.au/ng/wp-content/uploads/sites/106/2016/08/paper-1.pdf ... – or consider Algo

-- [The Register](https://twitter.com/TheRegister/status/825076303657177088)

> Algo is really easy and secure.

-- [the grugq](https://twitter.com/thegrugq/status/786249040228786176)
