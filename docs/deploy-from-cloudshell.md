# Deploy from Google Cloud Shell

If you want to try Algo but don't wish to install anything on your own system, you can use the **free** [Google Cloud Shell](https://cloud.google.com/shell/) to deploy a VPN to any supported cloud provider. Note that you cannot choose `Install to existing Ubuntu server` to turn Google Cloud Shell into your VPN server.

1. See the [Cloud Shell documentation](https://cloud.google.com/shell/docs/) to start an instance of Cloud Shell in your browser.

2. Get Algo and run it:
    ```bash
    git clone https://github.com/trailofbits/algo.git
    cd algo
    ./algo
    ```

    The first time you run `./algo`, it will automatically install all required dependencies. Google Cloud Shell already has most tools available, making this even faster than on your local system.

3. Once Algo has completed, retrieve a copy of the configuration files that were created to your local system. While still in the Algo directory, run:
    ```
    zip -r configs configs
    dl configs.zip
    ```

4. Unzip `configs.zip` on your local system and use the files to configure your VPN clients.
