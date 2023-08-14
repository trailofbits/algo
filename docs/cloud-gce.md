# Google Cloud Platform setup

* Follow the [`gcloud` installation instructions](https://cloud.google.com/sdk/)

* Log into your account using `gcloud init`

### Creating a project

The recommendation on GCP is to group resources into **Projects**, so we will create a new project for our VPN server and use a service account restricted to it.

```bash
## Create the project to group the resources
### You might need to change it to have a global unique project id
PROJECT_ID=${USER}-algo-vpn
BILLING_ID="$(gcloud beta billing accounts list --format="value(ACCOUNT_ID)")"

gcloud projects create ${PROJECT_ID} --name algo-vpn --set-as-default
gcloud beta billing projects link ${PROJECT_ID} --billing-account ${BILLING_ID}

## Create an account that have access to the VPN
gcloud iam service-accounts create algo-vpn --display-name "Algo VPN"
gcloud iam service-accounts keys create configs/gce.json \
  --iam-account algo-vpn@${PROJECT_ID}.iam.gserviceaccount.com
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member serviceAccount:algo-vpn@${PROJECT_ID}.iam.gserviceaccount.com \
  --role roles/compute.admin
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member serviceAccount:algo-vpn@${PROJECT_ID}.iam.gserviceaccount.com \
  --role roles/iam.serviceAccountUser

## Enable the services
gcloud services enable compute.googleapis.com

./algo -e "provider=gce" -e "gce_credentials_file=$(pwd)/configs/gce.json"

```

**Attention:** take care of the `configs/gce.json` file, which contains the credentials to manage your Google Cloud account, including create and delete servers on this project.


There are more advanced arguments available for deployment [using ansible](deploy-from-ansible.md).
