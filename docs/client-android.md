# Android client setup

## Installation via profiles

1. [Install the strongSwan VPN Client](https://play.google.com/store/apps/details?id=org.strongswan.android).
2. Copy `android_{username}.sswan` and `android_{username}_helper.html` to your phone's internal storage.
3. Open the helper file in a browser (e.g., Google Chrome).
4. Click on the link. It opens the StrongSwan app and configures the VPN with your profile.

## Manual installation

**NOTE:** If you are a Project Fi user, you must disable WiFi Assistant before continuing. See the [strongSwan documentation](https://wiki.strongswan.org/projects/strongswan/wiki/AndroidVPNClient) for details.

| Instruction | Screenshot(s) |
| ----------- | ---------- |
| 1. Copy your `{username}.p12` certificate to your phone's internal storage. | |
| 2. [Install the strongSwan VPN Client](https://play.google.com/store/apps/details?id=org.strongswan.android) (Android 4+) | |
| 3. Open the app and tap "ADD VPN PROFILE" in the top right.  | [![step3-thumb]][step3-screen]  |
| 4. Enter the IP address or hostname of your Algo server and set the "VPN Type" to "IKEv2 Certificate". | [![step4-thumb]][step4-screen] |
| 5. Tap "Select user certificate". You will be shown a prompt, tap "INSTALL". | [![step5-thumb]][step5-screen] |
| 6. Use the "Open from" menu to select your certificate. If you downloaded your certificate to your phone, you may find that using the "Downloads" shortcut results in your `{username}.p12` certificate being grayed out. If this happens go back to the "Open from" menu and tap on the name of your phone. This will bring up the filesystem. From here, navigate to the folder where you saved your cert (such as "Downloads"), and try again. | [![step6-thumb]][step6-screen] |
| 7. Enter the password for your certificate. This password was printed to your console at the end of running the `algo` deployment script. Please note that in some cases, extracting the certificate can take several minutes. | [![step7-thumb]][step7-screen] |
| 8. Give your certificate a name (it will default to your Algo username), and ensure that "Credential use" is set to "VPN and apps". Tap "OK". | [![step8-thumb]][step8-screen] |
| 9. You'll then be brought to another prompt. Ensure your newly imported certificate is selected, and tap "ALLOW". Then, tap "SAVE" in the top right. | [![step9-thumb]][step9-screen] |
| 10. You will be returned to the main menu, and your newly-configured VPN profile should be listed. Tap the profile to connect. | [![step10-thumb]][step10-screen] |

## Troubleshooting
### Tapping the VPN profile in strongSwan has no effect.
Ensure that "WiFi Assistant" and any other always-on VPNs are disabled before attempting to enable a strongSwan VPN. If any other VPN is active, strongSwan may silently fail to initialize a VPN connection. On Android 7, your can manage your VPNs by going to: Settings > Tap "More" under "Wireless & networks" > VPN > tap the gear icon next to any non-strongSwan VPNs listed and ensure they are disabled.


[step3-thumb]: https://i.imgur.com/LPwIGJE.png
[step4-thumb]: https://i.imgur.com/sFkDILg.png
[step5-thumb]: https://i.imgur.com/IliT5oD.png
[step6-thumb]: https://i.imgur.com/oghdCVp.png
[step7-thumb]: https://i.imgur.com/nDzJ7KS.png
[step8-thumb]: https://i.imgur.com/RPXSpCo.png
[step9-thumb]: https://i.imgur.com/uMinDPe.png
[step10-thumb]: https://i.imgur.com/hUEDjdo.png


[step3-screen]: https://i.imgur.com/xNMihCd.png
[step4-screen]: https://i.imgur.com/xYjoNNO.png
[step5-screen]: https://i.imgur.com/4qhKT1Z.png
[step6-screen]: https://i.imgur.com/MAaQuxH.png
[step7-screen]: https://i.imgur.com/aT2MPih.png
[step8-screen]: https://i.imgur.com/gvaKzkh.png
[step9-screen]: https://i.imgur.com/eZp8DNb.png
[step10-screen]: https://i.imgur.com/Nd8rYMJ.png
