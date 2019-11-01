# Local Installation

You can use Algo to configure a pre-existing server as an AlgoVPN rather than using it to create and configure a new server on a supported cloud provider. This is referred to as a **local** installation rather than a **cloud** deployment.

Install the Algo scripts following the normal installation instructions, then choose:
```
Install to existing Ubuntu 18.04, 19.04, or 19.10 server (Advanced)
```
Make sure your target server is running an unmodified copy of the operating system version specified. The target can be the same system where you've installed the Algo scripts, or a remote system that you are able to access as root via SSH without needing to enter the SSH key passphrase (such as when using `ssh-agent`).

**PLEASE NOTE**: Algo is intended for use to create a _dedicated_ VPN server. No uninstallation option is provided. If you install Algo on an existing server any existing services might break. In particular, the firewall rules will be overwritten. See [AlgoVPN and Firewalls](/docs/firewalls.md) for more information.
