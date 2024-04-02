# Linux strongSwan IPsec Clients (e.g., OpenWRT, Ubuntu Server, etc.)

Install strongSwan, then copy the included ipsec_user.conf, ipsec_user.secrets, user.crt (user certificate), and user.key (private key) files to your client device. These will require customization based on your exact use case. These files were originally generated with a point-to-point OpenWRT-based VPN in mind.

## Ubuntu Server example

1. `sudo apt-get install strongswan libstrongswan-standard-plugins`: install strongSwan
2. `/etc/ipsec.d/certs`: copy `<name>.crt` from `algo-master/configs/<server_ip>/ipsec/.pki/certs/<name>.crt`
3. `/etc/ipsec.d/private`: copy `<name>.key` from `algo-master/configs/<server_ip>/ipsec/.pki/private/<name>.key`
4. `/etc/ipsec.d/cacerts`: copy `cacert.pem` from `algo-master/configs/<server_ip>/ipsec/manual/cacert.pem`
5. `/etc/ipsec.secrets`: add your `user.key` to the list, e.g. `<server_ip> : ECDSA <name>.key`
6. `/etc/ipsec.conf`: add the connection from `ipsec_user.conf` and ensure `leftcert` matches the `<name>.crt` filename
7. `sudo ipsec restart`: pick up config changes
8. `sudo ipsec up <conn-name>`: start the ipsec tunnel
9. `sudo ipsec down <conn-name>`: shutdown the ipsec tunnel

One common use case is to let your server access your local LAN without going through the VPN. Set up a passthrough connection by adding the following to `/etc/ipsec.conf`:

    conn lan-passthrough
    leftsubnet=192.168.1.1/24 # Replace with your LAN subnet
    rightsubnet=192.168.1.1/24 # Replace with your LAN subnet
    authby=never # No authentication necessary
    type=pass # passthrough
    auto=route # no need to ipsec up lan-passthrough

To configure the connection to come up at boot time replace `auto=add` with `auto=start`.

## Notes on SELinux

If you use a system with SELinux enabled you might need to set appropriate file contexts:

````
semanage fcontext -a -t ipsec_key_file_t "$(pwd)(/.*)?"
restorecon -R -v $(pwd)
````

See [this comment](https://github.com/trailofbits/algo/issues/263#issuecomment-328053950).
