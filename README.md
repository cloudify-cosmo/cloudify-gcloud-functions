# cloudify-gcloud-functions
A repo for google functions used by Cloudify

### Deploying a function to Google Cloud:
From a function's directory:

`gcloud functions deploy <function name> --entry-point <entry point method name> --trigger-http --stage-bucket cloudify-functions --memory 256M --timeout 30`
