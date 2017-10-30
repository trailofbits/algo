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

We'll use the [rsclarke/NetworkManager-strongswan](https://copr.fedorainfracloud.org/coprs/rsclarke/NetworkManager-strongswan/) Copr repo (see [this comment](https://github.com/trailofbits/algo/issues/263#issuecomment-327820191)), this will make the `IKE` and `ESP` fields available in the Gnome Network Manager. Note that at time of writing the non-Copr repo will result in connection failures. Also note that the Copr repo *instructions are not filled in by author. Author knows what to do. Everybody else should avoid this repo*. So unless you are comfortable with using this repo, you'll want to hold out untill the patches applied in the Copr repo make it into stable.

First remove the stable `NetworkManager-strongswan` package, ensure you have backups in place and / or take note of config backups taken during the removal of the package.

````
dnf remove NetworkManager-strongswan
````

Next, enable the Copr repo and install it along with the `NetworkManager-strongswan-gnome` package:

````
dnf copr enable -y rsclarke/NetworkManager-strongswan
dnf install NetworkManager-strongswan NetworkManager-strongswan-gnome
````

Reboot your machine:

````
reboot now
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
    * Certificate: `cacert.pem` found at `/path/to/algo/1.2.3.4/cacert.pem`
  * Client:
    * Authentication: *Certificate/Private key*
    * Certificate: `user-name.crt` found at `/path/to/algo/1.2.3.4/pki/certs/user-name.crt` 
    * Private key: `user-name.key` found at `/path/to/algo/1.2.3.4/pki/private/user-name.key`
  * Options:
    * Check *Request an inner IP address*, connection will fail without this option
    * Optionally check *Enforce UDP encapsulation*
    * Optionally check *Use IP compression*
    * For the later 2 options, hover to option in the settings to see a description
  * Cipher proposal:
    * Check *Enable custom proposals*
    * IKE: `aes128gcm16-prfsha512-ecp256,aes128-sha2_512-prfsha512-ecp256,aes128-sha2_384-prfsha384-ecp256`
    * ESP: `aes128gcm16-ecp256,aes128-sha2_512-prfsha512-ecp256`
* Apply and turn the connection on, you should now be connected