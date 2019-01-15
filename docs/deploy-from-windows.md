# Windows client prerequisite

* 64-bit Windows 10 (Anniversary update or later version)

Once you verify your system is 64-bit (32-bit is not supported) and up to date, you have to do a few manual steps to enable the 'Windows Subsystem for Linux':

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


Install additional packages:

```shell
sudo apt-get update && sudo apt-get install git build-essential libssl-dev libffi-dev python-dev python-pip python-setuptools python-virtualenv -y
```

Clone the Algo repository:

```shell
cd ~ && git clone https://github.com/trailofbits/algo && cd algo
```

Now, you can go through the [README](https://github.com/trailofbits/algo#deploy-the-algo-server) (start from the 4th step) and deploy your Algo server!
