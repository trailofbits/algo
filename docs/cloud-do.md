# DigitalOcean cloud setup

## API Token creation

First, login into your DigitalOcean account.

Select **API** from the titlebar. This will take you to the "Applications & API" page.

![The Applications & API page](/docs/images/do-api.png)

On the **Tokens/Keys** tab, select **Generate New Token**. A dialog will pop up. In that dialog, give your new token a name, and make sure **Write** is checked off. Click the **Generate Token** button when you are ready.

![The new token dialog, showing a form requesting a name and confirmation on the scope for the new token.](/docs/images/do-new-token.png)

You will be returned to the **Tokens/Keys** tab, and your new key will be shown under the **Personal Access Tokens** header.

![The new token in the listing.](/docs/images/do-view-token.png)

Copy or note down the hash that shows below the name you entered, as this will be necessary for the steps below. This value will disappear if you leave this page, and you'll need to regenerate it if you forget it.

## Select a Droplet (optional)

The default option is the `s-1vcpu-1gb` because it is available in all regions. However, you may want to switch to a cheaper droplet such as `s-1vcpu-512mb-10gb` even though it is not available in all regions. This can be edited in the [Configuration File](config.cfg) under `cloud_providers > digitalocean > size`. See this brief comparison between the two droplets below:

| Droplet Type | Monthly Cost | Bandwidth | Availability |
|:--|:-:|:-:|:--|
| `s-1vcpu-512mb-10gb` | $4/month | 0.5 TB | Limited |
| `s-1vcpu-1gb`        | $6/month | 1.0 TB | All regions |
| ... | ... | ... | ... |

*Note: Exceeding bandwidth limits costs $0.01/GiB at time of writing ([docs](https://docs.digitalocean.com/products/billing/bandwidth/#droplets)). See the live list of droplets [here](https://slugs.do-api.dev/).*

## Using DigitalOcean with Algo (interactive)

These steps are for those who run Algo using Docker or using the `./algo` command.

Choose DigitalOcean as your provider:

```
What provider would you like to use?
    1. DigitalOcean
    2. Amazon Lightsail
    3. Amazon EC2
    4. Vultr
    5. Microsoft Azure
    6. Google Compute Engine
    7. Scaleway
    8. OpenStack (DreamCompute optimised)
    9. Install to existing Ubuntu server (Advanced)

Enter the number of your desired provider
:
1
```

Enter a name for your server. Leave this as the default if you are not certain how this will affect your setup:

```
Name the vpn server:
[algo]:
```

After several prompts related to Algo features you will be asked for the API Token value. Paste the API Token value you copied when following the steps in [API Token creation](#api-token-creation) (you won't see any output as the key is not echoed by Algo):

```
Enter your API token. The token must have read and write permissions (https://cloud.digitalocean.com/settings/api/tokens):
 (output is hidden):
```

Finally you will be asked the region in which you wish to setup your new Algo server. This list is dynamic and can change based on availability of resources. Enter the number next to name of the region:

```
What region should the server be located in?
    1. ams3     Amsterdam 3
    2. blr1     Bangalore 1
    3. fra1     Frankfurt 1
    4. lon1     London 1
    5. nyc1     New York 1
    6. nyc3     New York 3
    7. sfo2     San Francisco 2
    8. sgp1     Singapore 1
    9. tor1     Toronto 1

Enter the number of your desired region
[6]
:
9
```

## Using DigitalOcean with Algo (scripted)

If you are using Ansible directly to run Algo you will need to pass the API Token as `do_token`. For example:

```shell
ansible-playbook main.yml -e "provider=digitalocean
                                server_name=algo
                                ondemand_cellular=true
                                ondemand_wifi=true
                                dns_adblocking=false
                                ssh_tunneling=false
                                store_pki=true
                                region=nyc3
                                do_token=token"
```

For more, see [Scripted Deployment](deploy-from-ansible.md).

## Using the DigitalOcean firewall with Algo

Many cloud providers include the option to configure an external firewall between the Internet and your cloud server. For some providers this is mandatory and Algo will configure it for you, but for DigitalOcean the external firewall is optional. See [AlgoVPN and Firewalls](/docs/firewalls.md) for more information.

To configure the DigitalOcean firewall, go to **Networking**, **Firewalls**, and choose **Create Firewall**.

Configure your **Inbound Rules** as follows:

![Inbound Rules](/docs/images/do-firewall.png)

Leave the **Outbound Rules** at their defaults.

Under **Apply to Droplets** enter the tag `Environment:Algo` to apply this firewall to all current and future Algo VPNs you create.
