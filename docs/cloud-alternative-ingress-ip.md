# Alternative Ingress IP

This feature allows you to configure the Algo server to send outbound traffic through a different external IP address than the one you are establishing the VPN connection with.

![cloud-alternative-ingress-ip](/docs/images/cloud-alternative-ingress-ip.png)

Additional info might be found in [this issue](https://github.com/trailofbits/algo/issues/1047)




#### Caveats

##### Extra charges

- DigitalOcean: Floating IPs are free when assigned to a Droplet, but after manually deleting a Droplet you need to also delete the Floating IP or you'll get charged for it.

##### IPv6

Some cloud providers provision a VM with an `/128` address block size. This is the only IPv6 address provided and for outbound and incoming traffic.

If the provided address block size is bigger, e.g., `/64`, Algo takes a separate address than the one is assigned to the server to send outbound IPv6 traffic.
