# Windows client manual setup

Windows clients have a more complicated setup than most others. Follow the steps below to set one up:

1. Copy the CA certificate (`cacert.pem`), user certificate (`$user.p12`), and the user PowerShell script (`windows_$user.ps1`) to the client computer.
2. Import the CA certificate to the local machine Trusted Root certificate store.
3. Open PowerShell as Administrator. Navigate to your copied files.
4. If you haven't already, you will need to change the Execution Policy to allow unsigned scripts to run.

```powershell
Set-ExecutionPolicy Unrestricted -Scope CurrentUser
```

5. In the same PowerShell window, run the included PowerShell script to import the user certificate, set up a VPN connection, and activate stronger ciphers on it.
6. After you execute the user script, set the Execution Policy back before you close the PowerShell window.

```powershell
Set-ExecutionPolicy Restricted -Scope CurrentUser
```

Your VPN is now installed and ready to use.

If you want to perform these steps by hand, you will need to import the user certificate to the Personal certificate store, add an IKEv2 connection in the network settings, then activate stronger ciphers on it via the following PowerShell script:

```powershell
Set-VpnConnectionIPsecConfiguration -ConnectionName "Algo" -AuthenticationTransformConstants GCMAES128 -CipherTransformConstants GCMAES128 -EncryptionMethod AES128 -IntegrityCheckMethod SHA384 -DHGroup ECP256 -PfsGroup ECP256
```
