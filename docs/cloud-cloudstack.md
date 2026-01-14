### Configuration file

> **⚠️ Important Note:** Exoscale is no longer supported as they deprecated their CloudStack API on May 1, 2024. Please use alternative providers like Hetzner, DigitalOcean, Vultr, or Scaleway.

Algo scripts will ask you for the API details. You need to fetch the API credentials and the endpoint from your CloudStack provider's control panel.

For CloudStack providers, you'll need to set:

```bash
export CLOUDSTACK_KEY="<your api key>"
export CLOUDSTACK_SECRET="<your secret>"
export CLOUDSTACK_ENDPOINT="<your provider's API endpoint>"
```

Make sure your provider supports the CloudStack API. Contact your provider for the correct API endpoint URL.
