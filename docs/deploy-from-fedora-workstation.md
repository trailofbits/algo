# Deploy from Fedora Workstation

These docs were written based on experience on Fedora Workstation 26.

## Prerequisites

### DNF counterparts of apt packages

The following table lists `apt` packages with their `dnf` counterpart. This is purely informative.
Using `python2-*` in favour of `python3-*` as per [declared dependency](https://github.com/trailofbits/algo#deploy-the-algo-server).

| `apt` | `dnf` |
| ----- | ----- |
| `build-essential` | `make automake gcc gcc-c++ kernel-devel` |
| `libssl-dev` | `openssl-devel` |
| `libffi-dev` | `libffi-devel` |
| `python-dev` | `python-devel` |  
| `python-pip` | `python2-pip` |
| `python-setuptools` | `python2-setuptools` |
| `python-virtualenv` | `python2-virtualenv` |

### Install requirements

First, let's make sure our system is up-to-date:

````
dnf upgrade
````

Next, install the required packages:

````
dnf install -y \
  ansible \
  automake \
  gcc \
  gcc-c++ \
  kernel-devel \
  openssl-devel \
  libffi-devel \
  libselinux-python \
  python-devel \
  python2-pip \
  python2-setuptools \
  python2-virtualenv \
  make
````

## Get Algo


[Download](https://github.com/trailofbits/algo/archive/master.zip) or clone:

````
git clone git@github.com:trailofbits/algo.git
cd algo
````

If you downloaded Algo, unzip to your prefered location and `cd` into it.
We'll assume from this point forward that our working directory is the `algo` root directory.


## Prepare algo

Some steps are needed before we can deploy our Algo VPN server.

### Check `pip`

Run `pip -v` and check the python version it is using:
 
````
$ pip -V
pip 9.0.1 from /usr/lib/python2.7/site-packages (python 2.7)
````

`python 2.7` is what we're looking for.

### `pip` upgrade and installs

````
# Upgrade pip itself
pip -q install --upgrade pip
# python-devel needed to prevent setup.py crash
pip -q install pycrypto       
# pycrypto 2.7.1 needed for latest security patch
# This may need to run with sudo to complete without permission violations
pip -q install setuptools --upgrade
# virtualenv to make installing dependencies easier
pip -q install virtualenv
````

### Setup virtualenv and install requirements

````
virtualenv --system-site-packages env
source env/bin/activate
pip -q install --user -r requirements.txt
````

## Configure

Edit the userlist and any other settings you desire in `config.cfg` using your prefered editor.

## Deploy

We can now deploy our server by running:

````
./algo
````

Ensure to allow Windows / Linux clients when going through the config options.
Note the IP and password of the newly created Alfo VPN server and store it safely.

If you want to setup client config on your Fedora Workstation, refer to [the Linux Client docs](client-linux.md).

## Notes on SELinux

If you have SELinux enabled, you'll need to set appropriate file contexts:

````
semanage fcontext -a -t ipsec_key_file_t "$(pwd)(/.*)?"
restorecon -R -v $(pwd)
````

See [this comment](https://github.com/trailofbits/algo/issues/263#issuecomment-328053950).
