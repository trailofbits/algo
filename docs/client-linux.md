# Linux client setup

It's possible to deploy an ipsec connection on Linux clients.
Supported distributives are: Debian, Ubuntu, CentOS, Fedora

The playbook is `deploy_client.yml`

### Required variables:

* `client_ip` - The IP address of your client machine (You can use `localhost` in order to deploy locally)
* `vpn_user` - The username. (Ensure that you have valid certificates and keys in the `configs/SERVER_ip/pki/` directory)
* `client_ssh_user` - The username that we need to use in order to connect to the client machine via SSH (ignore if you are deploying locally)
* `server_ip` - The vpn server ip address

### Example:

```shell
ansible-playbook deploy_client.yml -e 'client_ip=client.com vpn_user=jack server_ip=vpn-server.com server_ssh_user=root'
```
