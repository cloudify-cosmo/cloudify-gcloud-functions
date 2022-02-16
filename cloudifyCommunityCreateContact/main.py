import json
import requests
import retrying

hubspot_api_key = "b800751d-61fc-42b7-8620-a55219976d43"
headers = {'Content-Type': 'application/json'}


def retrieve_contact_id_and_company(data):
    # try to get contact by email
    contact_url = 'https://api.hubapi.com/contacts/v1/contact/email/{}/' \
               'profile?hapikey={}'.format(data["email"], hubspot_api_key)
    get_resp = requests.get(url=contact_url, headers=headers)
    r_json = get_resp.json()
    if get_resp.ok:
         # contact already exists
         vid = r_json['vid']
         company = r_json['associated-company']['properties']['name']['value']
         return {"status": 200, "contact_id": vid, "company_name": company}
    if get_resp.status_code == 404:
         # contact doesn't exist yet
         vid = create_hubspot_contact(data)
         company = retrieve_company_name_from_hubspot(vid, hubspot_api_key)
         if company:
            return {"status": 200, "contact_id": vid, "company_name": company}
         return {"status": 400,
            "message": "could not retrieve company name from Hubspot"}
    return {"status": get_resp.status_code, "message": r_json['message']}


def create_hubspot_contact(data):
    create_url = "https://api.hubapi.com/contacts/v1/contact/?" \
                 "hapikey={}".format(hubspot_api_key)
    payload = {
        "properties": [
            {"property": "email", "value": data["email"]},
            {"property": "firstname", "value": data["firstname"]},
            {"property": "lastname", "value": data["lastname"]},
            {"property": "phone", "value": data["phone"]},
            {"property": "by_downloading_cloudify_you_agree_to_the_cloudify_"
                      "end_user_license_agreement",
            "value": data["is_eula"]},
        ]
    }
    post_resp = requests.post(data=json.dumps(payload), url=create_url,
                              headers={'Content-Type': 'application/json'})
    r_json = post_resp.json()
    if not post_resp.ok:
        return {"status": post_resp.status_code, "message": r_json['message']}
    return r_json['vid']


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
    result = retrieve_contact_id_and_company(request_json)
    return json.dumps(result)
