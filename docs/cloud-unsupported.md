# Local deployment

It is possible to download the Algo scripts to your own Ubuntu server and run the scripts locally. You need to install Ansible to run Algo on Ubuntu. Installing ansible via pip requires pulling in a lot of dependencies, including a full compiler suite. It would be easier to use apt, however, Ubuntu 16.04 only comes with Ansible 2.0.0.2. Therefore, to use apt you must use the ansible PPA, and using a PPA requires installing `software-properties-common`.

tl;dr:

```shell
sudo apt-get install software-properties-common && sudo apt-add-repository ppa:ansible/ansible
sudo apt-get update && sudo apt-get install ansible
git clone https://github.com/trailofbits/algo
cd algo && ./algo
```

**Warning**: If you run Algo on your existing server, the iptables rules will be overwritten. If you don't want to overwrite the rules, you must deploy via `ansible-playbook` and skip the `iptables` tag as described below.