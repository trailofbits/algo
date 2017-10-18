#!/usr/bin/env bash

set -e

ACTIVATE_SCRIPT="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )/env/bin/activate"
if [ -f "$ACTIVATE_SCRIPT" ]
then
	source $ACTIVATE_SCRIPT
else
	echo "$ACTIVATE_SCRIPT not found.  Did you follow documentation to install dependencies?"
	exit 1
fi

SKIP_TAGS="_null encrypted"
ADDITIONAL_PROMPT="[pasted values will not be displayed]"

additional_roles () {

read -p "
Do you want macOS/iOS clients to enable \"VPN On Demand\" when connected to cellular networks?
[y/N]: " -r OnDemandEnabled_Cellular
OnDemandEnabled_Cellular=${OnDemandEnabled_Cellular:-n}
if [[ "$OnDemandEnabled_Cellular" =~ ^(y|Y)$ ]]; then EXTRA_VARS+=" OnDemandEnabled_Cellular=Y"; fi

read -p "
Do you want macOS/iOS clients to enable \"VPN On Demand\" when connected to Wi-Fi?
[y/N]: " -r OnDemandEnabled_WIFI
OnDemandEnabled_WIFI=${OnDemandEnabled_WIFI:-n}
if [[ "$OnDemandEnabled_WIFI" =~ ^(y|Y)$ ]]; then EXTRA_VARS+=" OnDemandEnabled_WIFI=Y"; fi

if [[ "$OnDemandEnabled_WIFI" =~ ^(y|Y)$ ]]; then
  read -p "
List the names of trusted Wi-Fi networks (if any) that macOS/iOS clients exclude from using the VPN (e.g., your home network. Comma-separated value, e.g., HomeNet,OfficeWifi,AlgoWiFi)
: " -r OnDemandEnabled_WIFI_EXCLUDE
  OnDemandEnabled_WIFI_EXCLUDE=${OnDemandEnabled_WIFI_EXCLUDE:-_null}
  EXTRA_VARS+=" OnDemandEnabled_WIFI_EXCLUDE=\"$OnDemandEnabled_WIFI_EXCLUDE\""
fi

read -p "
Do you want to install a DNS resolver on this VPN server, to block ads while surfing?
[y/N]: " -r dns_enabled
dns_enabled=${dns_enabled:-n}
if [[ "$dns_enabled" =~ ^(y|Y)$ ]]; then ROLES+=" dns"; fi

read -p "
Do you want each user to have their own account for SSH tunneling?
[y/N]: " -r ssh_tunneling_enabled
ssh_tunneling_enabled=${ssh_tunneling_enabled:-n}
if [[ "$ssh_tunneling_enabled" =~ ^(y|Y)$ ]]; then ROLES+=" ssh_tunneling"; fi

read -p "
Do you want to apply operating system security enhancements on the server? (warning: replaces your sshd_config)
[y/N]: " -r security_enabled
security_enabled=${security_enabled:-n}
if [[ "$security_enabled" =~ ^(y|Y)$ ]]; then ROLES+=" security"; fi

read -p "
Do you want the VPN to support Windows 10 or Linux Desktop clients? (enables compatible ciphers and key exchange, less secure)
[y/N]: " -r Win10_Enabled
Win10_Enabled=${Win10_Enabled:-n}
if [[ "$Win10_Enabled" =~ ^(y|Y)$ ]]; then EXTRA_VARS+=" Win10_Enabled=Y"; fi

read -p "
Do you want to retain the CA key? (required to add users in the future, but less secure)
[y/N]: " -r Store_CAKEY
Store_CAKEY=${Store_CAKEY:-N}
if [[ "$Store_CAKEY" =~ ^(n|N)$ ]]; then EXTRA_VARS+=" Store_CAKEY=N"; fi

}

deploy () {

  ansible-playbook deploy.yml -t "${ROLES// /,}" -e "${EXTRA_VARS}" --skip-tags "${SKIP_TAGS// /,}"

}

azure () {
  read -p "
Enter your azure secret id (https://github.com/trailofbits/algo/blob/master/docs/cloud-azure.md)
You can skip this step if you want to use your defaults credentials from ~/.azure/credentials
$ADDITIONAL_PROMPT
[...]: " -rs azure_secret

  read -p "

Enter your azure tenant id (https://github.com/trailofbits/algo/blob/master/docs/cloud-azure.md)
You can skip this step if you want to use your defaults credentials from ~/.azure/credentials
$ADDITIONAL_PROMPT
[...]: " -rs azure_tenant

  read -p "

Enter your azure client id (application id) (https://github.com/trailofbits/algo/blob/master/docs/cloud-azure.md)
You can skip this step if you want to use your defaults credentials from ~/.azure/credentials
$ADDITIONAL_PROMPT
[...]: " -rs azure_client_id

  read -p "

Enter your azure subscription id (https://github.com/trailofbits/algo/blob/master/docs/cloud-azure.md)
You can skip this step if you want to use your defaults credentials from ~/.azure/credentials
$ADDITIONAL_PROMPT
[...]: " -rs azure_subscription_id

  read -p "

Name the vpn server:
[algo]: " -r azure_server_name
  azure_server_name=${azure_server_name:-algo}

  read -p "

  What region should the server be located in? (https://azure.microsoft.com/en-us/regions/)
    1.  South Central US
    2.  Central US
    3.  North Europe
    4.  West Europe
    5.  Southeast Asia
    6.  Japan West
    7.  Japan East
    8.  Australia Southeast
    9.  Australia East
    10. Canada Central
    11. West US 2
    12. West Central US
    13. UK South
    14. UK West
    15. West US
    16. Brazil South
    17. Canada East
    18. Central India
    19. East Asia
    20. Germany Central
    21. Germany Northeast
    22. Korea Central
    23. Korea South
    24. North Central US
    25. South India
    26. West India
    27. East US
    28. East US 2

Enter the number of your desired region:
[1]: " -r azure_region
  azure_region=${azure_region:-1}

  case "$azure_region" in
    1) region="southcentralus" ;;
    2) region="centralus" ;;
    3) region="northeurope" ;;
    4) region="westeurope" ;;
    5) region="southeastasia" ;;
    6) region="japanwest" ;;
    7) region="japaneast" ;;
    8) region="australiasoutheast" ;;
    9) region="australiaeast" ;;
    10) region="canadacentral" ;;
    11) region="westus2" ;;
    12) region="westcentralus" ;;
    13) region="uksouth" ;;
    14) region="ukwest" ;;
    15) region="westus" ;;
    16) region="brazilsouth" ;;
    17) region="canadaeast" ;;
    18) region="centralindia" ;;
    19) region="eastasia" ;;
    20) region="germanycentral" ;;
    21) region="germanynortheast" ;;
    22) region="koreacentral" ;;
    23) region="koreasouth" ;;
    24) region="northcentralus" ;;
    25) region="southindia" ;;
    26) region="westindia" ;;
    27) region="eastus" ;;
    28) region="eastus2" ;;
  esac

  ROLES="azure vpn cloud"
  EXTRA_VARS="azure_secret=$azure_secret azure_tenant=$azure_tenant azure_client_id=$azure_client_id azure_subscription_id=$azure_subscription_id azure_server_name=$azure_server_name ssh_public_key=$ssh_public_key region=$region"
}

digitalocean () {
  read -p "
Enter your API token. The token must have read and write permissions (https://cloud.digitalocean.com/settings/api/tokens):
$ADDITIONAL_PROMPT
: " -rs do_access_token

  read -p "

Name the vpn server:
[algo.local]: " -r do_server_name
  do_server_name=${do_server_name:-algo.local}

  read -p "

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
[7]: " -r region
  region=${region:-7}

  case "$region" in
    1) do_region="ams2" ;;
    2) do_region="ams3" ;;
    3) do_region="fra1" ;;
    4) do_region="lon1" ;;
    5) do_region="nyc1" ;;
    6) do_region="nyc2" ;;
    7) do_region="nyc3" ;;
    8) do_region="sfo1" ;;
    9) do_region="sfo2" ;;
    10) do_region="sgp1" ;;
    11) do_region="tor1" ;;
    12) do_region="blr1" ;;
  esac

ROLES="digitalocean vpn cloud"
EXTRA_VARS="do_access_token=$do_access_token do_server_name=$do_server_name do_region=$do_region"
}

ec2 () {
  read -p "
Enter your aws_access_key (http://docs.aws.amazon.com/general/latest/gr/managing-aws-access-keys.html)
Note: Make sure to use an IAM user with an acceptable policy attached (see https://github.com/trailofbits/algo/blob/master/docs/deploy-from-ansible.md).
$ADDITIONAL_PROMPT
[AKIA...]: " -rs aws_access_key

  read -p "

Enter your aws_secret_key (http://docs.aws.amazon.com/general/latest/gr/managing-aws-access-keys.html)
$ADDITIONAL_PROMPT
[ABCD...]: " -rs aws_secret_key

read -p "

Name the vpn server:
[algo]: " -r aws_server_name
  aws_server_name=${aws_server_name:-algo}

  read -p "

  What region should the server be located in?
    1.   us-east-1           US East (N. Virginia)
    2.   us-east-2           US East (Ohio)
    3.   us-west-1           US West (N. California)
    4.   us-west-2           US West (Oregon)
    5.   ap-south-1          Asia Pacific (Mumbai)
    6.   ap-northeast-2      Asia Pacific (Seoul)
    7.   ap-southeast-1      Asia Pacific (Singapore)
    8.   ap-southeast-2      Asia Pacific (Sydney)
    9.   ap-northeast-1      Asia Pacific (Tokyo)
    10.  eu-central-1        EU (Frankfurt)
    11.  eu-west-1           EU (Ireland)
    12.  eu-west-2           EU (London)
    13.  ca-central-1        Canada (Central)
    14.  sa-east-1           São Paulo
Enter the number of your desired region:
[1]: " -r aws_region
  aws_region=${aws_region:-1}

  case "$aws_region" in
    1) region="us-east-1" ;;
    2) region="us-east-2" ;;
    3) region="us-west-1" ;;
    4) region="us-west-2" ;;
    5) region="ap-south-1" ;;
    6) region="ap-northeast-2" ;;
    7) region="ap-southeast-1" ;;
    8) region="ap-southeast-2" ;;
    9) region="ap-northeast-1" ;;
    10) region="eu-central-1" ;;
    11) region="eu-west-1" ;;
    12) region="eu-west-2";;
    13) region="ca-central-1" ;;
    14) region="sa-east-1" ;;
  esac

  ROLES="ec2 vpn cloud"
  EXTRA_VARS="aws_access_key=$aws_access_key aws_secret_key=$aws_secret_key aws_server_name=$aws_server_name ssh_public_key=$ssh_public_key region=$region"
}

gce () {
  read -p "
Enter the local path to your credentials JSON file (https://support.google.com/cloud/answer/6158849?hl=en&ref_topic=6262490#serviceaccounts):
: " -r credentials_file

  read -p "

Name the vpn server:
[algo]: " -r server_name
  server_name=${server_name:-algo}

  read -p "

  What zone should the server be located in?
    1. Western US       (Oregon A)
    2. Western US       (Oregon B)
    3. Western US       (Oregon C)
    4. Central US       (Iowa A)
    5. Central US       (Iowa B)
    6. Central US       (Iowa C)
    7. Central US       (Iowa F)
    8. Eastern US       (Northern Virginia A)
    9. Eastern US       (Northern Virginia B)
    10. Eastern US      (Northern Virginia C)
    11. Eastern US      (South Carolina B)
    12. Eastern US      (South Carolina C)
    13. Eastern US      (South Carolina D)
    14. Western Europe  (Belgium B)
    15. Western Europe  (Belgium C)
    16. Western Europe  (Belgium D)
    17. Western Europe  (London A)
    18. Western Europe  (London B)
    19. Western Europe  (London C)
    20. Western Europe  (Frankfurt A)
    21. Western Europe  (Frankfurt B)
    22. Western Europe  (Frankfurt C)
    23. Southeast Asia  (Singapore A)
    24. Southeast Asia  (Singapore B)
    25. East Asia       (Taiwan A)
    26. East Asia       (Taiwan B)
    27. East Asia       (Taiwan C)
    28. Northeast Asia  (Tokyo A)
    29. Northeast Asia  (Tokyo B)
    30. Northeast Asia  (Tokyo C)
    31. Australia	(Sydney A)
    32. Australia	(Sydney B)
    33. Australia	(Sydney C)
    34. South America   (São Paulo A)
    35. South America   (São Paulo B)
    36. South America   (São Paulo C)
Please choose the number of your zone. Press enter for default (#14) zone.
[14]: " -r region
  region=${region:-14}

  case "$region" in
    1) zone="us-west1-a" ;;
    2) zone="us-west1-b" ;;
    3) zone="us-west1-c" ;;
    4) zone="us-central1-a" ;;
    5) zone="us-central1-b" ;;
    6) zone="us-central1-c" ;;
    7) zone="us-central1-f" ;;
    8) zone="us-east4-a" ;;
    9) zone="us-east4-b" ;;
    10) zone="us-east4-c" ;;
    11) zone="us-east1-b" ;;
    12) zone="us-east1-c" ;;
    13) zone="us-east1-d" ;;
    14) zone="europe-west1-b" ;;
    15) zone="europe-west1-c" ;;
    16) zone="europe-west1-d" ;;
    17) zone="europe-west2-a" ;;
    18) zone="europe-west2-b" ;;
    19) zone="europe-west2-c" ;;
    20) zone="europe-west3-a" ;;
    21) zone="europe-west3-b" ;;
    22) zone="europe-west3-c" ;;
    23) zone="asia-southeast1-a" ;;
    24) zone="asia-southeast1-b" ;;
    25) zone="asia-east1-a" ;;
    26) zone="asia-east1-b" ;;
    27) zone="asia-east1-c" ;;
    28) zone="asia-northeast1-a" ;;
    29) zone="asia-northeast1-b" ;;
    30) zone="asia-northeast1-c" ;;
    31) zone="australia-southeast1-a" ;;
    32) zone="australia-southeast1-b" ;;
    33) zone="australia-southeast1-c" ;;
    34) zone="southamerica-east1-a" ;;
    35) zone="southamerica-east1-b" ;;
    36) zone="southamerica-east1-c" ;;
  esac

  ROLES="gce vpn cloud"
  EXTRA_VARS="credentials_file=$credentials_file gce_server_name=$server_name ssh_public_key=$ssh_public_key zone=$zone max_mss=1316"
}

non_cloud () {
  read -p "
Enter the IP address of your server: (or use localhost for local installation)
[localhost]: " -r server_ip
  server_ip=${server_ip:-localhost}

  read -p "

What user should we use to login on the server? (note: passwordless login required, or ignore if you're deploying to localhost)
[root]: " -r server_user
  server_user=${server_user:-root}

if [ "x${server_ip}" = "xlocalhost" ]; then
	myip=""
else
	myip=${server_ip}
fi

  read -p "

Enter the public IP address of your server: (IMPORTANT! This IP is used to verify the certificate)
[$myip]: " -r IP_subject
  IP_subject=${IP_subject:-$myip}

if [ "x${IP_subject}" = "x" ]; then
	echo "no server IP given. exiting."
	exit 1
fi

  ROLES="local vpn"
  EXTRA_VARS="server_ip=$server_ip server_user=$server_user IP_subject_alt_name=$IP_subject"
  SKIP_TAGS+=" cloud update-alternatives"

  read -p "

Was this server deployed by Algo previously?
[y/N]: " -r Deployed_By_Algo
Deployed_By_Algo=${Deployed_By_Algo:-n}
if [[ "$Deployed_By_Algo" =~ ^(y|Y)$ ]]; then EXTRA_VARS+=" Deployed_By_Algo=Y"; fi

}

algo_provisioning () {
  echo -n "
  What provider would you like to use?
    1. DigitalOcean
    2. Amazon EC2
    3. Microsoft Azure
    4. Google Compute Engine
    5. Install to existing Ubuntu 16.04 server

Enter the number of your desired provider
: "

  read -r N

  case "$N" in
    1) digitalocean; ;;
    2) ec2; ;;
    3) azure; ;;
    4) gce; ;;
    5) non_cloud; ;;
    *) exit 1 ;;
  esac

  additional_roles
  deploy
}

user_management () {

  read -p "
Enter the IP address of your server: (or use localhost for local installation)
: " -r server_ip

  read -p "
What user should we use to login on the server? (note: passwordless login required, or ignore if you're deploying to localhost)
[root]: " -r server_user
  server_user=${server_user:-root}

read -p "
Do you want each user to have their own account for SSH tunneling?
[y/N]: " -r ssh_tunneling_enabled
ssh_tunneling_enabled=${ssh_tunneling_enabled:-n}

if [ "x${server_ip}" = "xlocalhost" ]; then
	myip=""
else
	myip=${server_ip}
fi

read -p "

Enter the public IP address of your server: (IMPORTANT! This IP is used to verify the certificate)
[$myip]: " -r IP_subject
IP_subject=${IP_subject:-$myip}

if [ "x${IP_subject}" = "x" ]; then
echo "no server IP given. exiting."
exit 1
fi

  read -p "
Enter the password for the private CA key:
$ADDITIONAL_PROMPT
: " -rs easyrsa_CA_password

ansible-playbook users.yml -e "server_ip=$server_ip server_user=$server_user ssh_tunneling_enabled=$ssh_tunneling_enabled IP_subject_alt_name=$IP_subject easyrsa_CA_password=$easyrsa_CA_password" -t update-users --skip-tags common
}

case "$1" in
  update-users) user_management ;;
  *) algo_provisioning ;;
esac
