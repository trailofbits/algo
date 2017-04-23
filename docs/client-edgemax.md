# Setting up an EdgeMax Client

Steps

1) Set up config.cfg
   * one single user
   * Uncomment ```edgemax_support``` and ```edgemax_lan_subnet``` and make sure the LAN subnet is correct and does not overlapt with ```vpn_network```
   * 
2) Copy over files to router and place them as follows. This will preserve the files if you upgrade the router image
   * config/<ALGO_IP>/ipsec_<USER>.* /config/user-data
   * config/<ALGO_IP>/pki/cacert.pem /config/auth/algo/cacerts/
   * config/<ALGO_IP>/pki/certs/*.crt /config/auth/algo/certs/
   * config/<ALGO_IP>/pki/private/<USER>.key /config/auth/algo/private/
3) SSH into the router and copy files from the config folder to the ipsec.d configuration folders. You will have to do this step every time you upgrade the router image.
   * /config/auth/algo/cacerts/cacert.pem /etc/ipsec.d/cacerts
   * /config/auth/algo/certs/* /etc/ipsec.d/certs
   * /config/auth/algo/private/* /etc/ipsec.d/private (needs sudo)
4) Still on the router, edit /config/config.boot and add the following:

    ``` 
    vpn {
        ipsec {
            auto-update 3600
            auto-firewall-nat-exclude disable
            include-ipsec-conf /config/user-data/ipsec_home.conf
            include-ipsec-secrets /config/user-data/ipsec_home.secrets
            logging {
                log-level 2
                log-modes net
            }

        }
    }
    ```
5) ```sudo ipsec restart```
6) ```sudo ipsec statusall``` - At this point you should see a shunted connection in the output. If not, stop and verify the above steps. Proceeding without the shunted connection will break local routing if the tunnel fails to come up
    ```
    Listening IP addresses:
      <CLIENT_ISP_PUBLIC_IP>
      <LAN_SUBNET_1>
      <LAN_SUBNET_2>
    Connections:
    ikev2-<ALGO_IP>:  %any...<ALGO_IP>  IKEv2, dpddelay=35s
    ikev2-<ALGO_IP>:   local:  [CN=home] uses public key authentication
    ikev2-<ALGO_IP>:    cert:  "CN=home"
    ikev2-<ALGO_IP>:   remote: [<ALGO_IP>] uses public key authentication
    ikev2-<ALGO_IP>:   child:  10.0.0.0/16 === 0.0.0.0/0 TUNNEL, dpdaction=clear
       lanbypass:  %any...%any  IKEv1
       lanbypass:   local:  uses public key authentication
       lanbypass:   remote: uses public key authentication
       lanbypass:   child:  10.0.0.0/16 === 10.0.0.0/16 PASS
    Shunted Connections:
       lanbypass:  10.0.0.0/16 === 10.0.0.0/16 PASS
    Security Associations (0 up, 0 connecting):
      none
    ```
7) ```sudo ipsec up ikev2-<ALGO_IP>``` - the tunnel should come up 
    ```
    @ubnt:/$ sudo ipsec status
    Shunted Connections:
       lanbypass:  10.0.0.0/16 === 10.0.0.0/16 PASS
    Security Associations (1 up, 0 connecting):
    ikev2-<ALGO_IP>[1]: ESTABLISHED 11 minutes ago, 24.18.46.13[CN=home]...<ALGO_IP>[<ALGO_IP>]
    ikev2-<ALGO_IP>{1}:  INSTALLED, TUNNEL, ESP in UDP SPIs: c5fbcf80_i cdffe66d_o
    ikev2-<ALGO_IP>{1}:   10.0.0.0/16 === 0.0.0.0/0
    ```
8) Now, we need to make sure that packets meant to go into the tunnel are not modified by SNAT rules. Go to the web inteface and under Firewall/Nat > NAT, update the masquarade rule to only filter for Destination = ALGO_IP. Below it what it looks like in the config.boot file/UI tree. THe second rule below is an example of how you can exclude a client's traffic comeletely from the tunnel. 
    ```
    nat {
            rule 5003 {
                description "masquerade for WAN"
                destination {
                    address <ALGO_IP>
                }
                log disable
                outbound-interface eth0
                protocol all
                type masquerade
            }
            rule 5005 {
                description "Masquerade for WAN - Xbox One"
                destination {
                }
                log disable
                outbound-interface eth0
                protocol tcp
                source {
                    address 10.0.0.35
                }
                type masquerade
            }
    }
    ```
9) You can try enabling ipsec hardware offload in the UI config tree under system. This seemsto be buggy and in some cases results in throughput lower than when offload is disabled - YMMV
    ```
        offload {
            hwnat disable
            ipsec enable
            ipv4 {
                forwarding enable
                gre disable
                vlan enable
            }
            ipv6 {
                forwarding enable
                vlan enable
            }
        }
        ```
