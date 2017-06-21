# Azure cloud setup

| Instruction | Screenshot(s) |
| ----------- | ---------- |
| 1. Go to https://portal.azure.com/ | |
| 2. Go to **Azure Active Directory**  | [![step2-thumb]][step2-screen] |
| 3. Go to **App registrations** and click to **Add**  | [![step3-thumb]][step3-screen]  |
| 4. Fill out the forms and click **Create** | [![step4-thumb]][step4-screen]  |
| 5. Click on the app name | [![step5-thumb]][step5-screen]  |
| 6. Copy and save somewhere the **Application ID** and click on **Keys**. | [![step6-thumb]][step6-screen]  |
| 7. Fill out the forms and click **Save**. Copy and save somewhere the **Secret ID** (the value) | [![step7-thumb]][step7-screen]  |
| 8. Go to the **Main menu**, **Azure Active Directory** and click on **Properties**. Copy and save somewhere the **Directory ID**  | [![step8-thumb]][step8-screen]  |
| 9. Go to the **Main menu**, **Subscriptions** and click on the subscription you want you use in Algo. Copy and save the subscription id from the **Overview** tab | [![step9-thumb]][step9-screen]  |
| 10. Go to the **Access control (IAM)** tab and click to **Add** | [![step10-thumb]][step10-screen]  |
| 11. Select a role (Contributor will enough for all)| [![step11-thumb]][step11-screen] |
| 12. Swith next to **Add users** and search by the **App name** (the name from the 4th step) and select it. | [![step12-thumb]][step12-screen]  |

Now you can use Environment Variables:

* AZURE_CLIENT_ID - from the 6th step
* AZURE_SECRET - from the 7th step
* AZURE_TENANT - from the 8th step
* AZURE_SUBSCRIPTION_ID - from the 9th step

or create the credentials file ``~/.azure/credentials`:

```
[default]
client_id=
secret=
tenant=
subscription_id=
```
or just pass those values to the Algo script

[step2-screen]: http://i.imgur.com/ENvSupE.png
[step3-screen]: http://i.imgur.com/sPLQaQe.jpg
[step4-screen]: http://i.imgur.com/di3xFCM.jpg
[step5-screen]: http://i.imgur.com/SipQyRA.jpg
[step6-screen]: http://i.imgur.com/RRTqV7C.jpg
[step7-screen]: http://i.imgur.com/ZnqJeVv.jpg
[step8-screen]: http://i.imgur.com/WAS8Ovl.png
[step9-screen]: http://i.imgur.com/IvTN7o1.jpg
[step10-screen]: http://i.imgur.com/j6dgo75.png
[step11-screen]: http://i.imgur.com/NUJ6k7i.jpg
[step12-screen]: http://i.imgur.com/VZv5qwb.jpg

[step2-thumb]: https://i.imgur.com/ENvSupEm.png
[step3-thumb]: https://i.imgur.com/sPLQaQem.jpg
[step4-thumb]: https://i.imgur.com/di3xFCMm.jpg
[step5-thumb]: https://i.imgur.com/SipQyRAm.jpg
[step6-thumb]: https://i.imgur.com/RRTqV7Cm.jpg
[step7-thumb]: https://i.imgur.com/ZnqJeVvm.jpg
[step8-thumb]: https://i.imgur.com/WAS8Ovlm.png
[step9-thumb]: https://i.imgur.com/IvTN7o1m.jpg
[step10-thumb]: https://i.imgur.com/j6dgo75m.png
[step11-thumb]: https://i.imgur.com/NUJ6k7im.jpg
[step12-thumb]: https://i.imgur.com/VZv5qwbm.jpg
