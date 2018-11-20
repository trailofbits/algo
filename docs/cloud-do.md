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

## Using DigitalOcean with Algo (command)

These steps are for people who run Algo using Docker or using the "algo" command.

First you will be asked which server type to setup. You would want to enter "1" to use DigitalOcean.

```
  What provider would you like to use?
    1. DigitalOcean
    2. Amazon Lightsail
    3. Amazon EC2
    4. Microsoft Azure
    5. Google Compute Engine
    6. Scaleway
    7. OpenStack (DreamCompute optimised)
    8. Install to existing Ubuntu 18.04 server

Enter the number of your desired provider
: 1
```

Next you will be asked for the API Token value. Paste the API Token value you copied when following the steps in [API Token creation](#api-token-creation) (don't worry if don't see any output, as the key input is hidden by Algo).

```
Enter your API token. The token must have read and write permissions (https://cloud.digitalocean.com/settings/api/tokens):
[pasted values will not be displayed]
:
```

You will be prompted for the server name to enter. Feel free to leave this as the default ("algo.local") if you are not certain how this will affect your setup.

```
Name the vpn server:
[algo.local]:
```

After entering the server name the script ask which region you wish to setup your new Algo instance in. Enter the number next to name of the region.

```
  What region should the server be located in?
    1.  Amsterdam        (Datacenter 2)
    2.  Amsterdam        (Datacenter 3)
    3.  Frankfurt
    4.  London
    5.  New York         (Datacenter 1)
    6.  New York         (Datacenter 2)
    7.  New York         (Datacenter 3)
    8.  San Francisco    (Datacenter 1)
    9.  San Francisco    (Datacenter 2)
    10. Singapore
    11. Toronto
    12. Bangalore
Enter the number of your desired region:
[7]: 11
```

You will then be asked the remainder of the setup questions.

## Using DigitalOcean with Algo (via Ansible)

If you are using Ansible to deploy to DigitalOcean, you will need to pass the API Token to Ansible as `do_token`.

For example,

    ansible-playbook deploy.yml -e 'provider=digitalocean do_token=my_secret_token'

Where "my_secret_token" is your API Token. For more references see [deploy-from-ansible](deploy-from-ansible.md)
