# Azure cloud setup

The easiest way to get started with the Azure CLI is by running it in an Azure Cloud Shell environment through your browser.  

Here you can find some information from [the official doc](https://docs.microsoft.com/en-us/cli/azure/get-started-with-azure-cli?view=azure-cli-latest). We put the essential commands together for simplest usage.

## Install azure-cli

- macOS ([link](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli-macos?view=azure-cli-latest)):
  ```bash
  $ brew update && brew install azure-cli
  ```

- Linux (deb-based) ([link](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli-apt?view=azure-cli-latest)):
  ```bash
  $ sudo apt-get update && sudo apt-get install \
      apt-transport-https \
      lsb-release \
      software-properties-common \
      dirmngr -y
  $ AZ_REPO=$(lsb_release -cs)
  $ echo "deb [arch=amd64] https://packages.microsoft.com/repos/azure-cli/ $AZ_REPO main" | \
      sudo tee /etc/apt/sources.list.d/azure-cli.list
  $ sudo apt-key --keyring /etc/apt/trusted.gpg.d/Microsoft.gpg adv \
      --keyserver packages.microsoft.com \
      --recv-keys BC528686B50D79E339D3721CEB3E94ADBE1229CF
  $ sudo apt-get update
  $ sudo apt-get install azure-cli
  ```

- Linux (rpm-based) ([link](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli-yum?view=azure-cli-latest)):
  ```bash
  $ sudo rpm --import https://packages.microsoft.com/keys/microsoft.asc
  $ sudo sh -c 'echo -e "[azure-cli]\nname=Azure CLI\nbaseurl=https://packages.microsoft.com/yumrepos/azure-cli\nenabled=1\ngpgcheck=1\ngpgkey=https://packages.microsoft.com/keys/microsoft.asc" > /etc/yum.repos.d/azure-cli.repo'
  $ sudo yum install azure-cli
  ```

- Windows ([link](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli-windows?view=azure-cli-latest)):  
  For Windows the Azure CLI is installed via an MSI, which gives you access to the CLI through the Windows Command Prompt (CMD) or PowerShell. When installing for Windows Subsystem for Linux (WSL), packages are available for your Linux distribution. [Download the MSI installer](https://aka.ms/installazurecliwindows)

If your OS is missing or to get more information see [the official doc](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli?view=azure-cli-latest)


## Sign in

1. Run the `login` command:
```bash
az login
```  

  If the CLI can open your default browser, it will do so and load a sign-in page.

  Otherwise, you need to open a browser page and follow the instructions on the command line to enter an authorization code after navigating to https://aka.ms/devicelogin in your browser.

2. Sign in with your account credentials in the browser.

There are ways to sign in non-interactively, which are covered in detail in [Sign in with Azure CLI](https://docs.microsoft.com/en-us/cli/azure/authenticate-azure-cli?view=azure-cli-latest).


**Now you are able to deploy an AlgoVPN instance without hassle**
