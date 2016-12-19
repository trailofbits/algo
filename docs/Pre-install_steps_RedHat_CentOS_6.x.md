# Algo pre-install steps for Red Hat/CentOS 6.x (currently 6.8)

There is still heavy use of RH/CentOS 6 (which are essentially the basis of Amazon Linux as well) due to stability and lack of systemd. But unfortunately, as a result there are a number of dated libraries, including python 2.6 and limitations. This script will allow end-to-end installation of Algo on a local (or cloud-based) RH/Cent 6 VM to deploy to cloud instances including Digital Ocean and AWS, with zero warnings or errors.

## Step 1: Prep for RH/CentOS 6.8/Amazon

```
yum -y -q update
yum -y -q install epel-release
```

Enable any kernel updates:

``reboot`` 

## Step 2: Install Ansible & launch Algo

Fix GPG key warnings during Ansible rpm install

``rpm --import https://dl.fedoraproject.org/pub/epel/RPM-GPG-KEY-EPEL-6``

Fix GPG key warning during offical Software Collections (SCL) package install

``rpm --import https://raw.githubusercontent.com/sclorg/centos-release-scl/master/centos-release-scl/RPM-GPG-KEY-CentOS-SIG-SCLo``

RH/Cent 6.x uses Python 2.6 by default, which is explicitly deprecated and produces many warnings and errors, so we will install a safe, non-invasive 2.7 tool set which has to be expressly enabled (and will not survive login sessions and reboots)

```
yum -y -q install centos-release-SCL   # install Software Collections Library (to enable Python 2.7)
# Won't take effect until explicitly enabled, per login session		
yum -y -q install python27-python-devel python27-python-setuptools python27-python-pip
yum -y -q install openssl-devel libffi-devel automake gcc gcc-c++ kernel-devel wget unzip ansible nano 

# Enable 2.7 default for this session (needs re-run beween logins & reboots)
# shellcheck disable=SC1091
source /opt/rh/python27/enable
# We're now defaulted to 2.7 

pip -q install --upgrade pip  # upgrade pip itself
pip -q install pycrypto       # python-devel needed to prevent setup.py crash, pycrypto 2.7.1 needed for latest security patch
pip -q install setuptools --upgrade

wget -q https://github.com/trailofbits/algo/archive/master.zip
unzip master.zip 
cd algo-master || echo "No Algo directory found" && exit

# Must be run from algo-master dir:
pip -q install -r requirements.txt	# install Algo local (pusher) dependencies

nano config.cfg
./algo
```

## Post-install OSX:

* Copy ./configs/*mobileconfig to your local Mac
* Install the VPN profile on your Mac (10.10+ required)
  * ``/usr/bin/profiles -I -F ./x.x.x.x_NAME.mobileconfig``
* To remove: ```/usr/bin/profiles -D -F ./x.x.x.x_NAME.mobileconfig```

The VPN connection will now appear under Networks (which can be pinned to the top menu bar if preferred)
