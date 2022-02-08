import json
import requests
import retrying

hubspot_api_key = "9457e05f-79e6-4695-900d-b29545069414"


def create_hubspot_contact(data):
    url = "https://api.hubapi.com/contacts/v1/contact/?hapikey={}".format(hubspot_api_key)
    payload = {
        "properties": [
            {
                "property": "email",
                "value": data["email"]
            },
            {
                "property": "firstname",
                "value": data["firstname"]
            },
            {
                "property": "lastname",
                "value": data["lastname"]
            },
            {
                "property": "phone",
                "value": data["phone"]
            },
        ]
    }
    post_resp = requests.post(data=json.dumps(payload), url=url,
                              headers={'Content-Type': 'application/json'})
    r_json = post_resp.json()
    if not post_resp.ok:
        return {"status": post_resp.status_code, "message": r_json['message']}
    vid = r_json['vid']
    company_name = retrieve_company_name_from_hubspot(vid, hubspot_api_key)
    if company_name:
        return {"status": post_resp.status_code,
                "contact_id": vid,
                "company_name": company_name}
    return {"status": 400,
            "message": "could not retrieve company name from Hubspot"}


@retrying.retry(wait_fixed=300, stop_max_attempt_number=15)
def retrieve_company_name_from_hubspot(vid, api_key):
    url = 'https://api.hubapi.com/contacts/v1/contact/vid/{}/' \
          'profile?hapikey={}'.format(vid, api_key)
    resp = requests.get(url=url, headers={'Content-Type': 'application/json'})
    if not resp.ok:
        return
    associated_company = resp.json()['associated-company']
    company_name = associated_company['properties']['name']['value']
    return company_name


def main(request):
    request_json = request.get_json(silent=True)
    result = create_hubspot_contact(request_json)
    return json.dumps(result)
