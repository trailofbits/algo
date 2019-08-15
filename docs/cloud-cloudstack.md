### Configuration file

You need to create a configuration file in INI format with your api key in `$HOME/.cloudstack.ini`

```
[cloudstack]
endpoint = <endpoint>
key = <your api key>
secret = <your secret>
timeout = 30
```

Example for Exoscale (European cloud provider exposing CloudStack API), visit https://portal.exoscale.com/u/<your@account>/account/profile/api to gather the required information:  
```
[exoscale]
endpoint = https://api.exoscale.com/compute
key = <your api key>
secret = <your secret>
timeout = 30
```
