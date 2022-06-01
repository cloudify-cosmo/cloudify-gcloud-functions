import json
import time
import requests

from google.cloud import bigquery

hubspot_api_key = "b800751d-61fc-42b7-8620-a55219976d43"
hubspot_api_base_url = "https://api.hubapi.com/contacts/v1/contact/vid/"


def update_hubspot_contact(data):
    url = "https://api.hubapi.com/contacts/v1/contact/vid/{}/" \
          "profile?hapikey={}".format(data["hubspot_id"], hubspot_api_key)

    first_login_ts = data["first_login"].isoformat()
    last_login_ts = data["last_login"].isoformat()

    payload = {
        "properties": [
            {"property": "first_login", "value": first_login_ts},
            {"property": "last_login", "value": last_login_ts},
            {"property": "Tenants", "value": data["tenants"]},
            {"property": "Users", "value": data["users"]},
            {"property": "Blueprints", "value": data["blueprints"]},
            {"property": "Deployments", "value": data["deployments"]},
            {"property": "Executions", "value": data["executions"]},
            {"property": "Secrets", "value": data["secrets"]},
            {"property": "AWS", "value": data["AWS"]},
            {"property": "GCP", "value": data["GCP"]},
            {"property": "Azure", "value": data["Azure"]},
            {"property": "Helm", "value": data["Helm"]},
            {"property": "Kubernetes", "value": data["Kubernetes"]},
            {"property": "Terraform", "value": data["Terraform"]},
        ]
    }
    post_resp = requests.post(data=json.dumps(payload), url=url,
                              headers={'Content-Type': 'application/json'})
    error_message = ""
    print("{}: {}".format(post_resp.status_code, data["hubspot_id"]))
    if not post_resp.ok:
        print("Error on sent data: {}".format(data))
        error_message = post_resp.json().get('message')
    return post_resp.status_code, error_message, payload


def query_data_usage():
    client = bigquery.Client()
    query = client.query(
        """
        select  a.metadata_customer_id,   
                SUBSTR(a.metadata_customer_id, -8) as hubspot_id, 
                a.cloudify_usage_first_login,
                a.cloudify_usage_last_login,
                a.cloudify_usage_tenants_count,
                a.cloudify_usage_users_count,
                a.cloudify_usage_blueprints_count,
                a.cloudify_usage_deployments_count,
                a.cloudify_usage_executions_count,
                a.cloudify_usage_secrets_count,
                CONTAINS_SUBSTR(a.cloudify_usage_nodes_by_type, 
                    'cloudify.nodes.aws') as aws_node_types,
                CONTAINS_SUBSTR(a.cloudify_usage_nodes_by_type, 
                    'cloudify.nodes.gcp') as gcp_node_types,
                REGEXP_CONTAINS(a.cloudify_usage_nodes_by_type, 
                    '(cloudify.azure.nodes|cloudify.nodes.azure)') 
                    as azure_node_types,
                CONTAINS_SUBSTR(a.cloudify_usage_nodes_by_type, 
                    'cloudify.nodes.helm') as helm_node_types,
                CONTAINS_SUBSTR(a.cloudify_usage_nodes_by_type, 
                    'cloudify.kubernetes') as kubernetes_node_types,
                CONTAINS_SUBSTR(a.cloudify_usage_nodes_by_type, 
                    'cloudify.nodes.terraform') as terraform_node_types
        from `omer-tenant.cloudify_usage.managers_usage` a
        inner join (select metadata_customer_id, 
                    MAX(metadata_timestamp) metadata_timestamp
                    from `omer-tenant.cloudify_usage.managers_usage` 
                    group by metadata_customer_id) b
        on (a.metadata_customer_id = b.metadata_customer_id and 
            a.metadata_timestamp = b.metadata_timestamp)
        where (a.metadata_customer_id like "CAS-%" 
            or a.metadata_customer_id like "COM-%")
        and timestamp_seconds(a.metadata_timestamp) >= 
            DATE_SUB(timestamp(CURRENT_DATE()), INTERVAL 2 DAY)
        """
    )
    query_results = query.result()  # Waits for job to complete.
    result = {}
    sync_data = []
    for row in query_results:
        payload = {
            "hubspot_id": row.hubspot_id,
            "first_login": row.cloudify_usage_first_login,
            "last_login": row.cloudify_usage_last_login,
            "tenants": row.cloudify_usage_tenants_count,
            "users": row.cloudify_usage_users_count,
            "blueprints": row.cloudify_usage_blueprints_count,
            "deployments": row.cloudify_usage_deployments_count,
            "executions": row.cloudify_usage_executions_count,
            "secrets": row.cloudify_usage_secrets_count,
            "AWS": row.aws_node_types,
            "GCP": row.gcp_node_types,
            "Azure": row.azure_node_types,
            "Helm": row.helm_node_types,
            "Kubernetes": row.kubernetes_node_types,
            "Terraform": row.terraform_node_types,
        }
        status_code, error_message, raw_request = \
            update_hubspot_contact(payload)
        result[row.hubspot_id] = status_code

        sync_data.append({
            "sync_timestamp": f"{time.time():.0f}",
            "contact_id": payload["hubspot_id"],
            "status": str(status_code),
            "error_message": error_message,
            "property_first_login": payload["first_login"],
            "property_last_login": payload["last_login"],
            "property_Tenants": payload["tenants"],
            "property_Users": payload["users"],
            "property_Blueprints": payload["blueprints"],
            "property_Deployments": payload["deployments"],
            "property_Executions": payload["executions"],
            "property_Secrets": payload["secrets"],
            "property_AWS": payload["AWS"],
            "property_GCP": payload["GCP"],
            "property_Azure": payload["Azure"],
            "property_Helm": payload["Helm"],
            "property_Kubernetes": payload["Kubernetes"],
            "property_Terraform": payload["Terraform"],
            "raw_request": raw_request,
        })

    # persist data sent to Hubspot in a dedicated table
    client = bigquery.Client()
    table_id = bigquery.Table.from_string(
        "omer-tenant.cloudify_usage.hubspot_usage_sync")
    table = client.get_table(table_id)
    client.insert_rows_json(table, sync_data)  # API request

    return result


def main(request, context):
    result = query_data_usage()
    return json.dumps(result)
