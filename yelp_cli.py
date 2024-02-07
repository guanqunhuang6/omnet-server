import requests
import json
import pdb

# read ./streamlit/secrets.toml
def read_toml(path):
    import toml
    with open(path, 'r') as f:
        config = toml.load(f)
    return config

if __name__ == '__main__':
    toml_file = read_toml('./.streamlit/secrets.toml')
    api_key = toml_file["YELP_API_KEY"]
    headers = {'Authorization': 'Bearer %s' % api_key}

    url='https://api.yelp.com/v3/businesses/matches'
    url_details='https://api.yelp.com/v3/businesses/'
    url_user_reviews='https://api.yelp.com/v3/businesses/{}/reviews'

    openai_response_json = {'Restaurant': 'Bottega Napa Valley', 
                            'Time': '2023-12-31T13:15:00', 
                            'Meal Type': 'Lunch', 
                            'Address1': '6525 Washington Street Suite A9', 
                            'city': 'Yountville', 
                            'state': 'CA', 
                            'Zip Code': '94599'}

    params = {
        'name': openai_response_json['Restaurant'],
        'address1': openai_response_json['Address1'],
        'city': openai_response_json['city'],
        'state': openai_response_json['state'],
        'country': 'US'
    }

    response = requests.get(url, headers=headers, params=params)

    if response.status_code == 200:
        businesses = json.loads(response.text)['businesses']
        for business in businesses:
            business_id = businesses[0]['id']
            response_details = requests.get(url_details + business_id, headers=headers)
            response_reviews = requests.get(url_user_reviews.format(business_id), headers=headers)
            pdb.set_trace()
    else:
        print(f"Request failed with status code {response.status_code}")
        
    