### Configuration file

Algo scripts will ask you for the API detail. You need to fetch the API credentials and the endpoint from the provider control panel.

Example for Exoscale (European cloud provider exposing CloudStack API), visit https://portal.exoscale.com/u/<your@account>/account/profile/api to gather the required information: CloudStack api key and secret.

```bash
export CLOUDSTACK_KEY="<your api key>"
export CLOUDSTACK_SECRET="<your secret>"
export CLOUDSTACK_ENDPOINT="https://api.exoscale.com/compute"
```
