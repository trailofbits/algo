# Deploy from Google Cloud Shell
**IMPORTANT NOTE: As of 2021-12-14 Algo requires Python 3.8, but Google Cloud Shell only provides Python 3.7.3. The instructions below will not work until Google updates Cloud Shell to have at least Python 3.8.**

If you want to try Algo but don't wish to install the software on your own system you can use the **free** [Google Cloud Shell](https://cloud.google.com/shell/) to deploy a VPN to any supported cloud provider. Note that you cannot choose `Install to existing Ubuntu server` to turn Google Cloud Shell into your VPN server.

1. See the [Cloud Shell documentation](https://cloud.google.com/shell/docs/) to start an instance of Cloud Shell in your browser.

2. Follow the [Algo installation instructions](https://github.com/trailofbits/algo#deploy-the-algo-server) as shown but skip step **3. Install Algo's core dependencies** as they are already installed. Run Algo to deploy to a supported cloud provider.

3. Once Algo has completed, retrieve a copy of the configuration files that were created to your local system. While still in the Algo directory, run:
    ```
    zip -r configs configs
    dl configs.zip
    ```

4. Unzip `configs.zip` on your local system and use the files to configure your VPN clients.
