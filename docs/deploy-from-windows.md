# Deploy from Windows

The Algo scripts can't be run directly on Windows, but you can use the Windows Subsystem for Linux (WSL) to run a copy of Ubuntu Linux right on your Windows system. You can then run Algo to deploy a VPN server to a supported cloud provider, though you can't turn the instance of Ubuntu running under WSL into a VPN server.

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
5. Restart Windows and then install [Ubuntu 20.04 LTS from the Windows Store](https://www.microsoft.com/p/ubuntu-2004-lts/9n6svws3rx71).
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

## Post installation steps

These steps should be only if you clone the Algo repository to the host machine disk (C:, D:, etc.). WSL mount host system disks to `\mnt` directory.

### Allow git to change files metadata

By default git cannot change files metadata (using chmod for example) for files stored at host machine disks (https://docs.microsoft.com/en-us/windows/wsl/wsl-config#set-wsl-launch-settings). Allow it:

1. Start Ubuntu Terminal.
2. Edit /etc/wsl.conf (create it if it doesn't exist). Add the following:
```
[automount]
options = "metadata"
```
3. Close all Ubuntu Terminals.
4. Run powershell.
5. Run `wsl --shutdown` in powershell.

### Allow  run Ansible in a world writable directory

Ansible threat host machine directories as world writable directory and do not load .cfg from it by default (https://docs.ansible.com/ansible/devel/reference_appendices/config.html#cfg-in-world-writable-dir). For fix run inside `algo` directory:

```shell
chmod 744 .
```

Now you can continue by following the [README](https://github.com/trailofbits/algo#deploy-the-algo-server) from the 4th step to deploy your Algo server!

You'll be instructed to edit the file `config.cfg` in order to specify the Algo user accounts to be created. If you're new to Linux the simplest editor to use is `nano`. To edit the file while in the `algo` directory, run:
```shell
nano config.cfg
```
Once `./algo` has finished you can use the `cp` command to copy the configuration files from the `configs` directory into your Windows directory under `/mnt/c/Users` for easier access.
