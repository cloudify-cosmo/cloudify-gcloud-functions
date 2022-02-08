# cloudify-gcloud-functions
A repo for google functions used by Cloudify

### Deploying a function to Google Cloud:
From a function's directory:

`gcloud functions deploy <function> --entry-point <entry_point> --trigger-http --stage-bucket cloudify-functions --memory 256M --timeout 30`

* <function> = name of the function that will be deployed on Google Cloud
* <entry_point> = name of the method inside the function's main/index file which serves as the entry-point for running the function
