# Deploy from Fedora Workstation

These docs were written based on experience on Fedora Workstation 30.

## Prerequisites

### DNF counterparts of apt packages

The following table lists `apt` packages with their `dnf` counterpart. This is purely informative.

| `apt` | `dnf` |
| ----- | ----- |
| `build-essential` | `make automake gcc gcc-c++ kernel-devel` |
| `libssl-dev` | `openssl-devel` |
| `libffi-dev` | `libffi-devel` |
| `python3-dev` | `python3-devel` |
| `python3-pip` | `python3-pip` |
| `python3-setuptools` | `python3-setuptools` |
| `python3-virtualenv` | `python3-virtualenv` |

### Install requirements

First, let's make sure our system is up-to-date:

````
dnf upgrade
````

Next, install the required packages:

````
dnf install -y \
  automake \
  gcc \
  gcc-c++ \
  kernel-devel \
  openssl-devel \
  libffi-devel \
  python3-devel \
  python3-pip \
  python3-setuptools \
  python3-virtualenv \
  python3-crypto \
  python3-pyyaml \
  python3-pyOpenSSL \
  python3-libselinux \
  make
````

## Get Algo


[Download](https://github.com/trailofbits/algo/archive/master.zip) or clone:

````
git clone https://github.com/trailofbits/algo.git
cd algo
````

If you downloaded Algo, unzip to your prefered location and `cd` into it.
We'll assume from this point forward that our working directory is the `algo` root directory.


## Prepare algo

Some steps are needed before we can deploy our Algo VPN server.

### Setup virtualenv and install requirements

```
python3 -m virtualenv --python="$(command -v python3)" .env
source .env/bin/activate
python3 -m pip install -U pip virtualenv
python3 -m pip install -r requirements.txt
```

## Configure

Edit the userlist and any other settings you desire in `config.cfg` using your prefered editor.

## Deploy

We can now deploy our server by running:

````
./algo
````

Note the IP and password of the newly created Algo VPN server and store it safely.

If you want to setup client config on your Fedora Workstation, refer to [the Linux Client docs](client-linux.md).

## Notes on SELinux

If you have SELinux enabled, you'll need to set appropriate file contexts:

````
semanage fcontext -a -t ipsec_key_file_t "$(pwd)(/.*)?"
restorecon -R -v $(pwd)
````

See [this comment](https://github.com/trailofbits/algo/issues/263#issuecomment-328053950).
