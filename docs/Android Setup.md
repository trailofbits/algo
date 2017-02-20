**NOTE:** If you are a Project Fi user, you must disable WiFi Assistant before continuing. See the [StrongSwan documentation](https://wiki.strongswan.org/projects/strongswan/wiki/AndroidVPNClient) for details.

| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Instruction&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; | Screenshot(s) |
| ----------- | ---------- |
| 1. Copy your `{username}.p12` certificate to your phone's internal storage. | |
| 2. [Install the StrongSwan VPN Client](https://play.google.com/store/apps/details?id=org.strongswan.android) (Android 4+) | |
| 3. Open the app and tap "ADD VPN PROFILE" in the top right.  | ![screenshot](https://i.imgur.com/xNMihCd.png)  |
| 4. Enter the IP address or hostname of your Algo server and set the "VPN Type" to "IKEv2 Certificate". | ![screenshot](https://i.imgur.com/xYjoNNO.png) |
| 5. Tap "Select user certificate". You will be shown a prompt, tap "INSTALL". | ![screenshot](https://i.imgur.com/4qhKT1Z.png) |
| 6. Use the "Open from" menu to select your certificate. If you downloaded your certificate to your phone, you may find that using the "Downloads" shortcut results in your `{username}.p12` certificate being grayed out. If this happens go back to the "Open from" menu and tap on the name of your phone. This will bring up the filesystem. From here, navigate to the folder where you saved your cert (such as "Downloads"), and try again. | ![screenshot](https://i.imgur.com/MAaQuxH.png) |
| 7. Enter the password for your certificate. This password was printed to your console at the end of running the `algo` deployment script. Please note that in some cases, extracting the certificate can take several minutes. | ![screenshot](https://i.imgur.com/aT2MPih.png) |
| 8. Give your certificate a name (it will default to your Algo username), and ensure that "Credential use" is set to "VPN and apps". Tap "OK". | ![screenshot](https://i.imgur.com/gvaKzkh.png) |
| 9. You'll then be brought to another prompt. Ensure your newly imported certificate is selected, and tap "ALLOW". Then, tap "SAVE" in the top right. | ![screenshot](https://i.imgur.com/eZp8DNb.png) |
| 10. You will be returned to the main menu, and your newly-configured VPN profile should be listed. Tap the profile to connect. | ![screenshot](https://i.imgur.com/Nd8rYMJ.png) |

## Troubleshooting
### Tapping the VPN profile in StrongSwan has no effect.
Ensure that "WiFi Assistant" and any other always-on VPNs are disabled before attempting to enable a StrongSwan VPN. If any other VPN is active, StrongSwan may silently fail to initialize a VPN connection. On Android 7, your can manage your VPNs by going to: Settings > Tap "More" under "Wireless & networks" > VPN > tap the gear icon next to any non-strongSwan VPNs listed and ensure they are disabled.
