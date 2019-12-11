# Deploy from Windows

The Algo scripts can't be run directly on Windows, but you can use the Windows Subsystem for Linux (WSL) to run a copy of Ubuntu Linux right on your Windows system.

To run WSL you will need:

* A 64-bit system
* 64-bit Windows 10 (Anniversary update or later version)

## Install WSL

Enable the 'Windows Subsystem for Linux':

1. Open 'Settings'
2. Click 'Update & Security', then click the 'For developers' option on the left.
3. Toggle the 'Developer mode' option, and accept any warnings Windows pops up.

Wait a minute for Windows to install a few things in the background (it will eventually let you know a restart may be required for changes to take effect—ignore that for now). Next, to install the actual Linux Subsystem, you have to jump over to 'Control Panel', and do the following:

1. Click on 'Programs'
2. Click on 'Turn Windows features on or off'
3. Scroll down and check 'Windows Subsystem for Linux', and then click OK.
4. The subsystem will be installed, then Windows will require a restart.
5. Restart Windows and then [install Ubuntu from the Windows Store](https://www.microsoft.com/p/ubuntu/9nblggh4msv6).
6. Run Ubuntu from the Start menu. It will take a few minutes to install. It will have you create a separate user account for the Linux subsystem. Once that's done, you will finally have Ubuntu running somewhat integrated with Windows.

## Install Algo

Run these commands in the Ubuntu Terminal to install a prerequisite package and download the Algo scripts to your home directory. Note that when using WSL you should **not** install Algo in the `/mnt/c` directory due to problems with file permissions.

You may need to follow [these directions](https://devblogs.microsoft.com/commandline/copy-and-paste-arrives-for-linuxwsl-consoles/) in order to paste commands into the Ubuntu Terminal.

```shell
cd
umask 0002
sudo apt update
sudo apt install -y python3-virtualenv
git clone https://github.com/trailofbits/algo
cd algo
```

Now you can continue by following the [README](https://github.com/trailofbits/algo#deploy-the-algo-server) from the 4th step to deploy your Algo server!

You'll be instructed to edit the file `config.cfg` in order to specify the Algo user accounts to be created. If you're new to Linux the simplest editor to use is `nano`. To edit the file while in the `algo` directory, run:
```shell
nano config.cfg
```
Once `./algo` has finished you can use the `cp` command to copy the configuration files from the `configs` directory into your Windows directory under `/mnt/c/Users` for easier access.
