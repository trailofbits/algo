# Using the built-in IPSEC VPN on Apple Devices

## Configure IPsec

Find the corresponding `mobileconfig` (Apple Profile) for each user and send it to them over AirDrop or other secure means. Apple Configuration Profiles are all-in-one configuration files for iOS and macOS devices. On macOS, double-clicking a profile to install it will fully configure the VPN. On iOS, users are prompted to install the profile as soon as the AirDrop is accepted.

## Enable the VPN

On iOS, connect to the VPN by opening **Settings** and clicking the toggle next to "VPN" near the top of the list. If using WireGuard you can also enable the VPN from the WireGuard app. On macOS, connect to the VPN by opening **System Preferences** -> **Network**, finding the Algo VPN in the left column, and clicking "Connect." Check "Show VPN status in menu bar" to easily connect and disconnect from the menu bar.

## Managing "Connect On Demand"

If you enabled "Connect On Demand" the VPN will connect automatically whenever it is able. Most Apple users will want to enable "Connect On Demand", but if you do then simply disabling the VPN will not cause it to stay disabled; it will just "Connect On Demand" again. To disable the VPN you'll need to disable "Connect On Demand".

On iOS, you can turn off "Connect On Demand" in **Settings** by clicking the (i) next to the entry for your Algo VPN and toggling off "Connect On Demand." On macOS, you can turn off "Connect On Demand" by opening **System Preferences** -> **Network**, finding the Algo VPN in the left column, unchecking the box for "Connect on demand", and clicking Apply.