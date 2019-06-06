# Linux client setup

## Provision client config

After you deploy a server, you can use an included Ansible script to provision Linux clients too! Debian, Ubuntu, CentOS, and Fedora are supported. The playbook is `deploy_client.yml`.

### Required variables

* `client_ip` - The IP address of your client machine (You can use `localhost` in order to deploy locally)
* `vpn_user` - The username. (Ensure that you have valid certificates and keys in the `configs/SERVER_ip/pki/` directory)
* `ssh_user` - The username that we need to use in order to connect to the client machine via SSH (ignore if you are deploying locally)
* `server_ip` - The vpn server ip address

### Example

```shell
ansible-playbook deploy_client.yml -e 'client_ip=client.com vpn_user=jack server_ip=vpn-server.com ssh_user=root'
```

### Additional options

If the user requires sudo password use the following argument: `--ask-become-pass`.

## OS Specific instructions

Some Linux clients may require more specific and details instructions to configure a connection to the deployed Algo VPN, these are documented here.

### Fedora Workstation

#### (Gnome) Network Manager install

First, install the required plugins.

````
dnf install NetworkManager-strongswan NetworkManager-strongswan-gnome
````

#### (Gnome) Network Manager configuration

In this example we'll assume the IP of our Algo VPN server is `1.2.3.4` and the user we created is `user-name`.

* Go to *Settings* > *Network*
* Add a new Network (`+` bottom left of the window)
* Select *IPsec/IKEv2 (strongswan)*
* Fill out the options:
  * Name: your choice, e.g.: *ikev2-1.2.3.4*
  * Gateway:
    * Address: IP of the Algo VPN server, e.g: `1.2.3.4`
    * Certificate: `cacert.pem` found at `/path/to/algo/configs/1.2.3.4/ipsec/.pki/cacert.pem`
  * Client:
    * Authentication: *Certificate/Private key*
    * Certificate: `user-name.crt` found at `/path/to/algo/configs/1.2.3.4/ipsec/.pki/certs/user-name.crt`
    * Private key: `user-name.key` found at `/path/to/algo/configs/1.2.3.4/ipsec/.pki/private/user-name.key`
  * Options:
    * Check *Request an inner IP address*, connection will fail without this option
    * Optionally check *Enforce UDP encapsulation*
    * Optionally check *Use IP compression*
    * For the later 2 options, hover to option in the settings to see a description
  * Cipher proposal:
    * Check *Enable custom proposals*
    * IKE: `aes256gcm16-prfsha512-ecp384`
    * ESP: `aes256gcm16-ecp384`
* Apply and turn the connection on, you should now be connected
