# Local deployment

You can use Algo to configure a local server as an AlgoVPN rather than create and configure a new server on a cloud provider.

Install the Algo scripts on your server and follow the normal installation instructions, then choose:
```
Install to existing Ubuntu 18.04 server (Advanced)
```
Make sure your server is running the operating system specified.

**PLEASE NOTE**: Algo is intended for use as a _dedicated_ VPN server. If you install Algo on an existing server, then any existing services might break. In particular, the firewall rules will be overwritten. See [AlgoVPN and Firewalls](/docs/firewalls.md) for more information.

If you don't want to overwrite the rules you must deploy via `ansible-playbook` and skip the `iptables` tag as described in [deploy-from-ansible.md](deploy-from-ansible.md), after which you'll need to implement the necessary rules yourself.
