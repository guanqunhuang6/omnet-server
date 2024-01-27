import os
# run this command on the terminal: export NOTION_INTEGRATION_API=secret
from pprint import pprint 
import pdb
from notion_client import Client
# read ./streamlit/secrets.toml
def read_toml(path):
    import toml
    with open(path, 'r') as f:
        config = toml.load(f)
    return config

if __name__ == '__main__':
    toml_file = read_toml('./.streamlit/secrets.toml')
    NOTION_PRIVATE_API_KEY = toml_file['NOTION_PRIVATE_API_KEY']
    notion_private_client = Client(auth=NOTION_PRIVATE_API_KEY)
    APP_DIRECTORY_DATABASE_ID = toml_file['APP_DIRECTORY_DATABASE_ID']
    response = notion_private_client.databases.query(
            database_id=APP_DIRECTORY_DATABASE_ID,
            filter={
                "property": "Email Sample",
                "checkbox": {
                    "equals": True,
                }
            }
        )
    
    pdb.set_trace()