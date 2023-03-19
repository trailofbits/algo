# Algo VPN

[![Twitter](https://img.shields.io/twitter/url/https/twitter.com/fold_left.svg?style=social&label=Follow%20%40AlgoVPN)](https://twitter.com/AlgoVPN)
[![](https://github.com/trailofbits/algo/workflows/Main/badge.svg?branch=master)](https://github.com/trailofbits/algo/actions)

Algo VPN is a set of Ansible scripts that simplify the setup of a personal WireGuard and IPsec VPN. It uses the most secure defaults available and works with common cloud providers. See our [release announcement](https://blog.trailofbits.com/2016/12/12/meet-algo-the-vpn-that-works/) for more information.

## Features

* Supports only IKEv2 with strong crypto (AES-GCM, SHA2, and P-256) for iOS, macOS, and Linux
* Supports [WireGuard](https://www.wireguard.com/) for all of the above, in addition to Android and Windows 10
* Generates .conf files and QR codes for iOS, macOS, Android, and Windows WireGuard clients
* Generates Apple profiles to auto-configure iOS and macOS devices for IPsec - no client software required
* Includes a helper script to add and remove users
* Blocks ads with a local DNS resolver (optional)
* Sets up limited SSH users for tunneling traffic (optional)
* Based on current versions of Ubuntu and strongSwan
* Installs to DigitalOcean, Amazon Lightsail, Amazon EC2, Vultr, Microsoft Azure, Google Compute Engine, Scaleway, OpenStack, CloudStack, Hetzner Cloud, Linode, or [your own Ubuntu server (for more advanced users)](docs/deploy-to-ubuntu.md)

## Anti-features

* Does not support legacy cipher suites or protocols like L2TP, IKEv1, or RSA
* Does not install Tor, OpenVPN, or other risky servers
* Does not depend on the security of [TLS](https://tools.ietf.org/html/rfc7457)
* Does not claim to provide anonymity or censorship avoidance
* Does not claim to protect you from the [FSB](https://en.wikipedia.org/wiki/Federal_Security_Service), [MSS](https://en.wikipedia.org/wiki/Ministry_of_State_Security_(China)), [DGSE](https://en.wikipedia.org/wiki/Directorate-General_for_External_Security), or [FSM](https://en.wikipedia.org/wiki/Flying_Spaghetti_Monster)

## Deploy the Algo Server

The easiest way to get an Algo server running is to run it on your local system or from [Google Cloud Shell](docs/deploy-from-cloudshell.md) and let it set up a _new_ virtual machine in the cloud for you.

1. **Setup an account on a cloud hosting provider.** Algo supports [DigitalOcean](https://m.do.co/c/4d7f4ff9cfe4) (most user friendly), [Amazon Lightsail](https://aws.amazon.com/lightsail/), [Amazon EC2](https://aws.amazon.com/), [Vultr](https://www.vultr.com/), [Microsoft Azure](https://azure.microsoft.com/), [Google Compute Engine](https://cloud.google.com/compute/), [Scaleway](https://www.scaleway.com/), [DreamCompute](https://www.dreamhost.com/cloud/computing/), [Linode](https://www.linode.com), or other OpenStack-based cloud hosting, [Exoscale](https://www.exoscale.com) or other CloudStack-based cloud hosting,  or [Hetzner Cloud](https://www.hetzner.com/).

2. **Get a copy of Algo.** The Algo scripts will be installed on your local system. There are two ways to get a copy:

    - Download the [ZIP file](https://github.com/trailofbits/algo/archive/master.zip). Unzip the file to create a directory named `algo-master` containing the Algo scripts.

    - Use `git clone` to create a directory named `algo` containing the Algo scripts:
        ```bash
        git clone https://github.com/trailofbits/algo.git
        ```

3. **Install Algo's core dependencies.** Algo requires that **Python 3.8 or later** and at least one supporting package are installed on your system.

    - **macOS:** Catalina (10.15) and higher includes Python 3 as part of the optional Command Line Developer Tools package. From Terminal run:

        ```bash
        python3 -m pip install --user --upgrade virtualenv
        ```

        If prompted, install the Command Line Developer Tools and re-run the above command.

        For macOS versions prior to Catalina, see [Deploy from macOS](docs/deploy-from-macos.md) for information on installing Python 3 .

    - **Linux:** Recent releases of Ubuntu, Debian, and Fedora come with Python 3 already installed. Make sure your system is up-to-date and install the supporting package(s):
        * Ubuntu and Debian:
            ```bash
            sudo apt install -y --no-install-recommends python3-virtualenv
            ```
            On a Raspberry Pi running Ubuntu also install `libffi-dev` and `libssl-dev`.

        * Fedora:
            ```bash
            sudo dnf install -y python3-virtualenv
            ```

    - **Windows:** Use the Windows Subsystem for Linux (WSL) to create your own copy of Ubuntu running under Windows from which to install and run Algo. See the [Windows documentation](docs/deploy-from-windows.md) for more information.

4. **Install Algo's remaining dependencies.** You'll need to run these commands from the Algo directory each time you download a new copy of Algo. In a Terminal window `cd` into the `algo-master` (ZIP file) or `algo` (`git clone`) directory and run:
    ```bash
    python3 -m virtualenv --python="$(command -v python3)" .env &&
      source .env/bin/activate &&
      python3 -m pip install -U pip virtualenv &&
      python3 -m pip install -r requirements.txt
    ```
    On Fedora first run `export TMPDIR=/var/tmp`, then add the option `--system-site-packages` to the first command above (after `python3 -m virtualenv`). On macOS install the C compiler if prompted.

5. **Set your configuration options.** Open the file `config.cfg` in your favorite text editor. Specify the users you wish to create in the `users` list. Create a unique user for each device you plan to connect to your VPN. 
 > Note: [IKEv2 Only] If you want to add or delete users later, you **must** select `yes` at the `Do you want to retain the keys (PKI)?` prompt during the server deployment. You should also review the other options before deployment, as changing your mind about them later [may require you to deploy a brand new server](https://github.com/trailofbits/algo/blob/master/docs/faq.md#i-deployed-an-algo-server-can-you-update-it-with-new-features).

6. **Start the deployment.** Return to your terminal. In the Algo directory, run `./algo` and follow the instructions. There are several optional features available, none of which are required for a fully functional VPN server. These optional features are described in greater detail in [here](docs/deploy-from-ansible.md).

That's it! You will get the message below when the server deployment process completes. Take note of the p12 (user certificate) password and the CA key in case you need them later, **they will only be displayed this time**.

You can now set up clients to connect to your VPN. Proceed to [Configure the VPN Clients](#configure-the-vpn-clients) below.

```
    "#                          Congratulations!                            #"
    "#                     Your Algo server is running.                     #"
    "#    Config files and certificates are in the ./configs/ directory.    #"
    "#              Go to https://whoer.net/ after connecting               #"
    "#        and ensure that all your traffic passes through the VPN.      #"
    "#                     Local DNS resolver 172.16.0.1                    #"
    "#        The p12 and SSH keys password for new users is XXXXXXXX       #"
    "#        The CA key password is XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX       #"
    "#      Shell access: ssh -F configs/<server_ip>/ssh_config <hostname>  #"
```

## Configure the VPN Clients

Certificates and configuration files that users will need are placed in the `configs` directory. Make sure to secure these files since many contain private keys. All files are saved under a subdirectory named with the IP address of your new Algo VPN server.

### Apple Devices

WireGuard is used to provide VPN services on Apple devices. Algo generates a WireGuard configuration file, `wireguard/<username>.conf`, and a QR code, `wireguard/<username>.png`, for each user defined in `config.cfg`.

On iOS, install the [WireGuard](https://itunes.apple.com/us/app/wireguard/id1441195209?mt=8) app from the iOS App Store. Then, use the WireGuard app to scan the QR code or AirDrop the configuration file to the device.

On macOS Mojave or later, install the [WireGuard](https://itunes.apple.com/us/app/wireguard/id1451685025?mt=12) app from the Mac App Store. WireGuard will appear in the menu bar once you run the app. Click on the WireGuard icon, choose **Import tunnel(s) from file...**, then select the appropriate WireGuard configuration file.

On either iOS or macOS, you can enable "Connect on Demand" and/or exclude certain trusted Wi-Fi networks (such as your home or work) by editing the tunnel configuration in the WireGuard app. (Algo can't do this automatically for you.)

Installing WireGuard is a little more complicated on older version of macOS. See [Using macOS as a Client with WireGuard](docs/client-macos-wireguard.md).

If you prefer to use the built-in IPSEC VPN on Apple devices, or need "Connect on Demand" or excluded Wi-Fi networks automatically configured, then see [Using Apple Devices as a Client with IPSEC](docs/client-apple-ipsec.md).

### Android Devices

WireGuard is used to provide VPN services on Android. Install the [WireGuard VPN Client](https://play.google.com/store/apps/details?id=com.wireguard.android). Import the corresponding `wireguard/<name>.conf` file to your device, then setup a new connection with it. See the [Android setup instructions](/docs/client-android.md) for more detailed walkthrough.

### Windows

WireGuard is used to provide VPN services on Windows. Algo generates a WireGuard configuration file, `wireguard/<username>.conf`, for each user defined in `config.cfg`.

Install the [WireGuard VPN Client](https://www.wireguard.com/install/#windows-7-8-81-10-2012-2016-2019). Import the generated `wireguard/<username>.conf` file to your device, then setup a new connection with it.

### Linux WireGuard Clients

WireGuard works great with Linux clients. See [this page](docs/client-linux-wireguard.md) for an example of how to configure WireGuard on Ubuntu.

### Linux strongSwan IPsec Clients (e.g., OpenWRT, Ubuntu Server, etc.)

Please see [this page](docs/client-linux-ipsec.md).

### OpenWrt Wireguard Clients

Please see [this page](docs/client-openwrt-router-wireguard.md).

### Other Devices

Depending on the platform, you may need one or multiple of the following files.

* ipsec/manual/cacert.pem: CA Certificate
* ipsec/manual/<user>.p12: User Certificate and Private Key (in PKCS#12 format)
* ipsec/manual/<user>.conf: strongSwan client configuration
* ipsec/manual/<user>.secrets: strongSwan client configuration
* ipsec/apple/<user>.mobileconfig: Apple Profile
* wireguard/<user>.conf: WireGuard configuration profile
* wireguard/<user>.png: WireGuard configuration QR code

## Setup an SSH Tunnel

If you turned on the optional SSH tunneling role, then local user accounts will be created for each user in `config.cfg` and SSH authorized_key files for them will be in the `configs` directory (user.ssh.pem). SSH user accounts do not have shell access, cannot authenticate with a password, and only have limited tunneling options (e.g., `ssh -N` is required). This ensures that SSH users have the least access required to setup a tunnel and can perform no other actions on the Algo server.

Use the example command below to start an SSH tunnel by replacing `<user>` and `<ip>` with your own. Once the tunnel is setup, you can configure a browser or other application to use 127.0.0.1:1080 as a SOCKS proxy to route traffic through the Algo server:

```bash
ssh -D 127.0.0.1:1080 -f -q -C -N <user>@algo -i configs/<ip>/ssh-tunnel/<user>.pem -F configs/<ip>/ssh_config
```

## SSH into Algo Server

Your Algo server is configured for key-only SSH access for administrative purposes. Open the Terminal app, `cd` into the `algo-master` directory where you originally downloaded Algo, and then use the command listed on the success message:

```
ssh -F configs/<ip>/ssh_config <hostname>
```

where `<ip>` is the IP address of your Algo server. If you find yourself regularly logging into the server then it will be useful to load your Algo ssh key automatically. Add the following snippet to the bottom of `~/.bash_profile` to add it to your shell environment permanently:

```
ssh-add ~/.ssh/algo > /dev/null 2>&1
```

Alternatively, you can choose to include the generated configuration for any Algo servers created into your SSH config. Edit the file `~/.ssh/config` to include this directive at the top:

```
Include <algodirectory>/configs/*/ssh_config
```

where `<algodirectory>` is the directory where you cloned Algo.

## Adding or Removing Users

_If you chose to save the CA key during the deploy process,_ then Algo's own scripts can easily add and remove users from the VPN server.

1. Update the `users` list in your `config.cfg`
2. Open a terminal, `cd` to the algo directory, and activate the virtual environment with `source .env/bin/activate`
3. Run the command: `./algo update-users`

After this process completes, the Algo VPN server will contain only the users listed in the `config.cfg` file.

## Additional Documentation
* [FAQ](docs/faq.md)
* [Troubleshooting](docs/troubleshooting.md)
* How Algo uses [Firewalls](docs/firewalls.md)

### Setup Instructions for Specific Cloud Providers
* Configure [Amazon EC2](docs/cloud-amazon-ec2.md)
* Configure [Azure](docs/cloud-azure.md)
* Configure [DigitalOcean](docs/cloud-do.md)
* Configure [Google Cloud Platform](docs/cloud-gce.md)
* Configure [Vultr](docs/cloud-vultr.md)
* Configure [CloudStack](docs/cloud-cloudstack.md)
* Configure [Hetzner Cloud](docs/cloud-hetzner.md)

### Install and Deploy from Common Platforms
* Deploy from [macOS](docs/deploy-from-macos.md)
* Deploy from [Windows](docs/deploy-from-windows.md)
* Deploy from [Google Cloud Shell](docs/deploy-from-cloudshell.md)
* Deploy from a [Docker container](docs/deploy-from-docker.md)

### Setup VPN Clients to Connect to the Server
* Setup [Android](docs/client-android.md) clients
* Setup [Linux](docs/client-linux.md) clients with Ansible
* Setup Ubuntu clients to use [WireGuard](docs/client-linux-wireguard.md)
* Setup Linux clients to use [IPsec](docs/client-linux-ipsec.md)
* Setup Apple devices to use [IPsec](docs/client-apple-ipsec.md)
* Setup Macs running macOS 10.13 or older to use [WireGuard](docs/client-macos-wireguard.md)

### Advanced Deployment
* Deploy to your own [Ubuntu](docs/deploy-to-ubuntu.md) server, and road warrior setup
* Deploy from [Ansible](docs/deploy-from-ansible.md) non-interactively
* Deploy onto a [cloud server at time of creation with shell script or cloud-init](docs/deploy-from-script-or-cloud-init-to-localhost.md)
* Deploy to an [unsupported cloud provider](docs/deploy-to-unsupported-cloud.md)
* Deploy to your own [FreeBSD](docs/deploy-to-freebsd.md) server

If you've read all the documentation and have further questions, [create a new discussion](https://github.com/trailofbits/algo/discussions).

## Endorsements

> I've been ranting about the sorry state of VPN svcs for so long, probably about
> time to give a proper talk on the subject. TL;DR: use Algo.

-- [Kenn White](https://twitter.com/kennwhite/status/814166603587788800)

> Before picking a VPN provider/app, make sure you do some research
> https://research.csiro.au/ng/wp-content/uploads/sites/106/2016/08/paper-1.pdf ... – or consider Algo

-- [The Register](https://twitter.com/TheRegister/status/825076303657177088)

> Algo is really easy and secure.

-- [the grugq](https://twitter.com/thegrugq/status/786249040228786176)

> I played around with Algo VPN, a set of scripts that let you set up a VPN in the cloud in very little time, even if you don’t know much about development. I’ve got to say that I was quite impressed with Trail of Bits’ approach.

-- [Romain Dillet](https://twitter.com/romaindillet/status/851037243728965632) for [TechCrunch](https://techcrunch.com/2017/04/09/how-i-made-my-own-vpn-server-in-15-minutes/)

> If you’re uncomfortable shelling out the cash to an anonymous, random VPN provider, this is the best solution.

-- [Thorin Klosowski](https://twitter.com/kingthor) for [Lifehacker](http://lifehacker.com/how-to-set-up-your-own-completely-free-vpn-in-the-cloud-1794302432)

## Support Algo VPN
[![Flattr](https://button.flattr.com/flattr-badge-large.png)](https://flattr.com/submit/auto?fid=kxw60j&url=https%3A%2F%2Fgithub.com%2Ftrailofbits%2Falgo)
[![PayPal](https://www.paypalobjects.com/en_US/i/btn/btn_donate_SM.gif)](https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=CYZZD39GXUJ3E)
[![Patreon](https://img.shields.io/badge/back_on-patreon-red.svg)](https://www.patreon.com/algovpn)
[![Bountysource](https://img.shields.io/bountysource/team/trailofbits/activity.svg)](https://www.bountysource.com/teams/trailofbits)

All donations support continued development. Thanks!

* We accept donations via [PayPal](https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=CYZZD39GXUJ3E), [Patreon](https://www.patreon.com/algovpn), and [Flattr](https://flattr.com/submit/auto?fid=kxw60j&url=https%3A%2F%2Fgithub.com%2Ftrailofbits%2Falgo).
* Use our [referral code](https://m.do.co/c/4d7f4ff9cfe4) when you sign up to Digital Ocean for a $10 credit.
* We also accept and appreciate contributions of new code and bugfixes via Github Pull Requests.

Algo is licensed and distributed under the AGPLv3. If you want to distribute a closed-source modification or service based on Algo, then please consider <a href="mailto:opensource@trailofbits.com">purchasing an exception</a> . As with the methods above, this will help support continued development.
