# RedHat/CentOS 6.x pre-installation requirements

Many people prefer RedHat or CentOS 6 (or similar variants like Amazon Linux) for to their stability and lack of systemd. Unfortunately, there are a number of dated libraries, notably Python 2.6, that prevent Algo from running without errors. This script will prepare a RedHat, CentOS, or similar VM to deploy to Algo cloud instances.

## Step 1: Prep for RH/CentOS 6.8/Amazon

```shell
yum -y update
yum -y install epel-release
```

Enable any kernel updates:

```shell
reboot
```

## Step 2: Install Ansible and launch Algo

RedHat/CentOS 6.x uses Python 2.6 by default, which is explicitly deprecated and produces many warnings and errors, so we must install a safe, non-invasive 3.6 tool set which has to be expressly enabled (and will not survive login sessions and reboots):

- Install the Software Collections Library (to enable Python 3.6)  
```shell
yum -y install centos-release-SCL
yum -y install \
  openssl-devel \
  libffi-devel \
  automake \
  gcc \
  gcc-c++ \
  kernel-devel \
  rh-python36-python \
  rh-python36-python-devel \
  rh-python36-python-setuptools \
  rh-python36-python-pip \
  rh-python36-python-virtualenv \
  rh-python36-python-crypto \
  rh-python36-PyYAML \
  libselinux-python \
  python-crypto \
  wget \
  unzip \
  nano
```

- 3.6 will not be used until explicitly enabled, per login session. Enable 3.6 default for this session (needs re-run between logins & reboots)  
```
scl enable rh-python36 bash
```

- We're now defaulted to 3.6. Upgrade required components  
```
python3 -m pip install -U pip virtualenv pycrypto setuptools
```

- Download and uzip Algo  
```
wget https://github.com/trailofbits/algo/archive/master.zip
unzip master.zip
cd algo-master || echo "No Algo directory found"
```

- Set up a virtualenv and install the local Algo dependencies (must be run from algo-master)  
```
python3 -m virtualenv --python="$(command -v python3)" .env
source .env/bin/activate
python3 -m pip install -U pip virtualenv
python3 -m pip install -r requirements.txt
```

- Edit the userlist and any other settings you desire  
```
nano config.cfg
```

- Now you can run the Algo installer!  
```
./algo
```

## Post-install macOS

1. Copy `./configs/*mobileconfig` to your local Mac

2. Install the VPN profile on your Mac (10.10+ required)

    ```shell
    /usr/bin/profiles -I -F ./x.x.x.x_NAME.mobileconfig
    ```

3. To remove:

    ```shell
    /usr/bin/profiles -D -F ./x.x.x.x_NAME.mobileconfig
    ```

The VPN connection will now appear under Networks (which can be pinned to the top menu bar if preferred)
