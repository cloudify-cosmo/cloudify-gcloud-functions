# cloudify-gcloud-functions
A repo for google functions used by Cloudify

### Deploying a function to Google Cloud:
From a function's directory:

`gcloud beta functions deploy <function> --entry-point <entry_point> 
--trigger-http --stage-bucket cloudify-functions --memory 256M --timeout 30`

* `<function>` = name of the function that will be deployed on Google Cloud
* `<entry_point>` = name of the method inside the function's main/index file which serves as the entry-point for running the function

#### Notes:
* **cloudifyHubspotContactUsage** is a scheduled function, and expects --trigger-topic CONTACT_USAGE`
* the Hubspot functions expect a secret `hubspot_pat` to be enabled for 
  the function as an environment variable. See [here](https://cloud.google.com/functions/docs/configuring/secrets) 
  on how to do it.<br>In the CLI command, the secret can be set using 
  `--set-secrets 'hubspot_pat=hubspot_pat:latest'`
