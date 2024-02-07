import streamlit as st
from streamlit.logger import get_logger
from httpx_oauth.oauth2 import BaseOAuth2
from typing import Any, Dict, List, Optional, Tuple, cast
import pdb
LOGGER = get_logger(__name__)


import streamlit as st
from streamlit_oauth import OAuth2Component
import extra_streamlit_components as stx
import os
import base64
import json
from pprint import pprint 
# from notion_db import NOTION_PRIVATE_API_KEY, NOTION_USER_DATABASE_ID
from notion_client import Client

NOTION_PRIVATE_API_KEY = st.secrets["NOTION_PRIVATE_API_KEY"]
NOTION_USER_DATABASE_ID = st.secrets["NOTION_USER_DATABASE_ID"]
APP_DIRECTORY_DATABASE_ID = st.secrets["APP_DIRECTORY_DATABASE_ID"]
PUBLIC_RESTAURANT_DATABASE_ID = st.secrets["PUBLIC_RESTAURANT_DATABASE_ID"]
notion_private_client = Client(auth=NOTION_PRIVATE_API_KEY)

# response = notion_private_client.databases.query(
#             database_id=NOTION_USER_DATABASE_ID,
#             filter={
#                 "property": "email",
#                 "title": {
#                     "equals": "guanqunhuang6@gmail.com"
#                 }
#             }
#         )
# pdb.set_trace()

st.set_page_config(
    page_title="omnet",
    page_icon=":robot:",
)

# @st.cache_resource(experimental_allow_widgets=True) 
# def get_manager():
#     return stx.CookieManager()
# cookie_manager = get_manager()

def oauth_google():
    st.title("Google Gmail Oauth2")
    CLIENT_ID = st.secrets["G_CLIENT_ID"]
    CLIENT_SECRET = st.secrets["G_CLIENT_SECRET"]
    AUTHORIZE_ENDPOINT = "https://accounts.google.com/o/oauth2/v2/auth"
    TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"
    REVOKE_ENDPOINT = "https://oauth2.googleapis.com/revoke"
    
    # if not cookie_manager.get(cookie="google_auth") and "google_auth" not in st.session_state:
    if "google_auth" not in st.session_state:
        # create a button to start the OAuth2 flow
        google_oauth2 = OAuth2Component(CLIENT_ID, CLIENT_SECRET, AUTHORIZE_ENDPOINT, TOKEN_ENDPOINT, TOKEN_ENDPOINT, REVOKE_ENDPOINT)
        google_result = google_oauth2.authorize_button(
            name="Continue with Google",
            icon="https://www.google.com.tw/favicon.ico",
            redirect_uri="https://omnet-server-aw0qwg29mdv.streamlit.app/",
            scope="openid email profile https://www.googleapis.com/auth/gmail.readonly",
            key="google",
            extras_params={"prompt": "consent", "access_type": "offline"},
            use_container_width=True,
        )

        if google_result:
            st.write(google_result)
            # decode the id_token jwt and get the user's email address
            id_token = google_result["token"]["id_token"]
            # verify the signature is an optional step for security
            payload = id_token.split(".")[1]
            # add padding to the payload if needed
            payload += "=" * (-len(payload) % 4)
            payload = json.loads(base64.b64decode(payload))
            email = payload["email"]
            st.session_state["google_auth"] = email
            st.session_state["google_token"] = google_result["token"]
            
            # st.set_cookie("google_auth", st.session_state["google_auth"])
            # st.set_cookie("google_token", st.session_state["google_token"])
            
            # cookie_manager.set("google_auth", st.session_state["google_auth"])
            # cookie_manager.set("google_token", st.session_state["google_token"])
            st.rerun()
    else:
        st.write("You are logged in with google!")
        # st.write(st.session_state["google_auth"])
        # st.write(st.session_state["google_token"])
        response = notion_private_client.databases.query(
            database_id=NOTION_USER_DATABASE_ID,
            filter={
                "property": "email",
                "title": {
                    "equals": st.session_state["google_auth"]
                }
            }
        )
        if len(response["results"]) == 0:
            notion_private_client.pages.create(
                parent={"database_id": NOTION_USER_DATABASE_ID},
                properties={
                    "email": {
                        "title": [
                            {
                                "text": {
                                    "content": st.session_state["google_auth"]
                                }
                            }
                        ]
                    },
                    "google_access_token": {
                        "rich_text": [
                            {
                                "text": {
                                    "content": st.session_state["google_token"]["access_token"]
                                }
                            }
                        ]
                    },
                    "google_refresh_token":{
                        "rich_text": [
                            {
                                "text": {
                                    "content": st.session_state["google_token"]["refresh_token"]
                                }
                            }
                        ]
                    }
                }
            )
        else:
            page_id = response["results"][0]["id"]
            notion_private_client.pages.update(
                page_id=page_id,
                properties={
                    "email": {
                        "title": [
                            {
                                "text": {
                                    "content": st.session_state["google_auth"]
                                }
                            }
                        ]
                    },
                    "google_access_token": {
                        "rich_text": [
                            {
                                "text": {
                                    "content": st.session_state["google_token"]["access_token"]
                                }
                            }
                        ]
                    },
                    "google_refresh_token":{
                        "rich_text": [
                            {
                                "text": {
                                    "content": st.session_state["google_token"]["refresh_token"]
                                }
                            }
                        ]
                    }
                }
            )

def oauth_notion():
    NOTION_OAUTH2_CLIENT_ID = st.secrets["NOTION_OAUTH2_CLIENT_ID"]
    NOTION_OAUTH2_CLIENT_SECRET = st.secrets["NOTION_OAUTH2_CLIENT_SECRET"]
    NOTION_OAUTH2_AUTHORIZATION_URL = "https://api.notion.com/v1/oauth/authorize"
    NOTION_OAUTH2_TOKEN_URL = "https://api.notion.com/v1/oauth/token"


    class NotionOAuth2(BaseOAuth2):
        def __init__(
            self,
            client_id: str,
            client_secret: str,
            **kwargs: Any,
        ) -> None:
            super().__init__(
                client_id,
                client_secret,
                NOTION_OAUTH2_AUTHORIZATION_URL,
                NOTION_OAUTH2_TOKEN_URL,
                NOTION_OAUTH2_TOKEN_URL,
                NOTION_OAUTH2_TOKEN_URL,
                **kwargs,
            )

        # override get_access_token to use Notion's custom OAuth2 flow
        async def get_access_token(
            self, code: str, redirect_uri: Optional[str] = None
        ) -> Dict[str, Any]:
            async with self.get_httpx_client() as client:
                data = {
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": redirect_uri,
                }
                basic_auth = self.client_id + ":" + self.client_secret
                # base64 encode the basic auth string
                basic_auth = base64.b64encode(basic_auth.encode("ascii")).decode("ascii")
                headers = {
                    "Authorization": f"Basic {basic_auth}",
                    "Content-Type": "application/json",
                }
                response = await client.post(self.access_token_endpoint, headers=headers, json=data, timeout=30) 
                if response.status_code != 200:
                    raise Exception(response.text)
                response.raise_for_status()
                return cast(Dict[str, Any], response.json())

    st.title("Notion OAuth2")

    notion_oauth_client = NotionOAuth2(NOTION_OAUTH2_CLIENT_ID, NOTION_OAUTH2_CLIENT_SECRET)

    # create an OAuth2Component instance
    notion_oauth2 = OAuth2Component(
        # client_id=None,
        # client_secret=None,
        # authorize_endpoint=None,
        # token_endpoint=None,
        # refresh_token_endpoint=None,
        # revoke_token_endpoint=None,
        client=notion_oauth_client,
    )


    if "notion_token" not in st.session_state:
        
        # create a button to start the OAuth2 flow
        notion_result = notion_oauth2.authorize_button(
            name="Login with Notion",
            icon="https://www.notion.so/images/favicon.ico",
            redirect_uri="https://omnet-server-aw0qwg29mdv.streamlit.app/",
            scope="user",
            key="notion",
            extras_params={"owner": "user"},
            use_container_width=True,
        )

        if notion_result:
            st.session_state["notion_token"] = notion_result
            st.rerun()
    else:
        st.write("You are logged in with notion!")
        # st.write(st.session_state["notion_token"])
        # st.button("Logout")
        # del st.session_state["notion_token"]
        if "google_auth" in st.session_state and "notion_update" not in st.session_state:
            response = notion_private_client.databases.query(
                database_id=NOTION_USER_DATABASE_ID,
                filter={
                    "property": "email",
                    "title": {
                        "equals": st.session_state["google_auth"]
                    }
                }
            )
            # response = notion_private_client.databases.query(
            #     database_id=NOTION_USER_DATABASE_ID,
            #     filter={
            #         "property": "email",
            #         "title": {
            #             "equals": st.session_state["google_auth"]
            #         }
            #     }
            # )
            if len(response["results"]) == 0:
                st.write("please login with google first, otherwise we will not update your notion database")
            else:
                page_id = response["results"][0]["id"]
                notion_private_client.pages.update(
                    page_id=page_id,
                    properties={
                        "notion_access_token": {
                            "rich_text": [
                                {
                                    "text": {
                                        "content": st.session_state["notion_token"]["token"]["access_token"]
                                    }
                                }
                            ]
                        },
                        "notion_workspace_id":{
                            "rich_text": [
                                {
                                    "text": {
                                        "content": st.session_state["notion_token"]["token"]["workspace_id"]
                                    }
                                }
                            ]
                        },
                        "notion_template_id":{
                            "rich_text": [
                                {
                                    "text": {
                                        "content": st.session_state["notion_token"]["token"]["duplicated_template_id"]
                                    }
                                }
                            ]
                        }
                    }
                )
                st.session_state["notion_update"] = True
        
from gmail import OmnetGmail
from openai_cli import OpenAIClient

openai_config = {
    'OPENAI_API_KEY': st.secrets["OPENAI_API_KEY"],
    # 'GPT_MODEL': "gpt-3.5-turbo-0613"
    'GPT_MODEL': 'gpt-4-1106-preview'
}
openai_client = OpenAIClient(openai_config)

def import_gmail():
    if st.button("Import Gmail"):
        gmail_config = {
            'email_address': st.session_state["google_auth"],
            'access_token': st.session_state["google_token"]["access_token"],
            'refresh_token': st.session_state["google_token"]["refresh_token"],
            'client_id': st.secrets["G_CLIENT_ID"],
            'client_secret': st.secrets["G_CLIENT_SECRET"],
            
        }
        omnet_gmail = OmnetGmail(gmail_config)
        ## find email database in template notion page
        if "google_auth" in st.session_state:
            response = notion_private_client.databases.query(
                database_id=NOTION_USER_DATABASE_ID,
                filter={
                    "property": "email",
                    "title": {
                        "equals": st.session_state["google_auth"]
                    }
                }
            )
            if len(response["results"]) == 0:
                st.write("please login with google first, otherwise we will not update your notion database")
            else:
                notion_access_token = response["results"][0]["properties"]["notion_access_token"]["rich_text"][0]["text"]["content"]
                notion_template_id = response["results"][0]["properties"]["notion_template_id"]["rich_text"][0]["text"]["content"]
                notion_user_client = Client(auth=notion_access_token)
                omnet_response = notion_user_client.blocks.children.list(block_id=notion_template_id)
                for result in omnet_response["results"]:
                    if result['type'] == "toggle":
                        source_databases_id = result['id']
                        break
                source_databases = notion_user_client.blocks.children.list(block_id=source_databases_id)
                for result in source_databases["results"]:
                    if result['child_database']['title'] == "Emails":
                        email_page_id = result['id']
                    elif result['child_database']['title'] == "Restaurants":
                        restaurant_page_id = result['id']
                    elif result['child_database']['title'] == "Meals":
                        meals_page_id = result['id']
                    else:
                        pass
                    
                ## Get app directory from database
                app_directory_response = notion_private_client.databases.query(
                    database_id=APP_DIRECTORY_DATABASE_ID,
                    filter={
                        "property": "Email Sample",
                        "checkbox": {
                            "equals": True,
                        }
                    }
                )
                for app_directory_result in app_directory_response["results"]:
                    transactional_email = app_directory_result["properties"]["Transactional Email"]['email']
                    key_words = app_directory_result["properties"]["Key String"]['rich_text'][0]['text']['content']
                    # print(transactional_email, key_words)
                    messages = omnet_gmail.get_from_specific_email(transactional_email)
                    for message in messages:
                        meta_data, content = omnet_gmail.get_content_from_id(message['id'])
                        if key_words in meta_data['subject']:
                            
                            ## write into email database for user 
                            notion_user_client.pages.create(
                                parent={ 'database_id': email_page_id },
                                properties={
                                    'Subject': { 'rich_text': [{ 'type': 'text', 'text': { 'content': meta_data['subject'] }}] },
                                    'Sender': { 'email': transactional_email},
                                    'Receiver': { 'email': meta_data['receiver']},
                                    'Date': { 'date': { 'start': meta_data['date'],}},
                                    'Email Content': { 'rich_text': [{ 'type': 'text', 'text': { 'content': content[:2000] }}] },
                                },
                            )
                            
                            ## write into other database from email database 
                            content = "'email_subject': " + meta_data['subject'] + ", 'email_content': " + content
                            openai_response = openai_client.extract_info_from_email(content)
                            
                            openai_response_json = json.loads(openai_response.tool_calls[0].function.arguments)

                            # public_restaurant_response = notion_private_client.databases.query(
                            #     database_id=PUBLIC_RESTAURANT_DATABASE_ID,
                            #     filter={
                            #         "and": [
                            #             {
                            #                 "property": "Name",
                            #                 "title": {
                            #                     "equals": openai_response_json['Restaurant']
                            #                 }
                            #             },
                            #             {
                            #                 "property": "Zip Code",
                            #                 "rich_text": {
                            #                     "equals": openai_response_json['Zip Code']
                            #                 }
                            #             }
                            #         ]
                            #     }
                            # )
                            
                            # if len(public_restaurant_response["results"]) == 0:
                            #     public_restaurant_row_response = notion_private_client.pages.create(
                            #         parent={ 'database_id': PUBLIC_RESTAURANT_DATABASE_ID },
                            #         properties={
                            #             'Name': { 'title': [{ 'type': 'text', 'text': { 'content': openai_response_json['Restaurant'] }}] },
                            #             'Zip Code':  { 'rich_text': [{ 'type': 'text', 'text': { 'content': openai_response_json['Zip Code'] }}] },
                            #         },
                            #     )
                            #     public_restaurant_row_page_id = public_restaurant_row_response['id']
                            # else:
                            #     public_restaurant_row_page_id = public_restaurant_response["results"][0]["id"]
                            
                            restaurant_response = notion_user_client.databases.query(
                                database_id=restaurant_page_id,
                                filter={
                                    "property": "Name",
                                    "title": {
                                        "equals": openai_response_json['Restaurant']
                                    }
                                }
                            )
                            if len(restaurant_response["results"]) == 0:
                                restaurant_row_response = notion_user_client.pages.create(
                                    parent={ 'database_id': restaurant_page_id },
                                    properties={
                                        'Name': { 'title': [{ 'type': 'text', 'text': { 'content': openai_response_json['Restaurant'] }}] },
                                        'Price Range': { 'rich_text': [{ 'type': 'text', 'text': { 'content': "$$" }}] },
                                        'Address': { 'rich_text': [{ 'type': 'text', 'text': { 'content': openai_response_json['Address1'] + ", "+ openai_response_json['city'] + ", " + openai_response_json['state'] }}] },
                                    },
                                )
                            else:
                                pass
                            
                            ## write into notion Meals database
                            notion_user_client.pages.create(
                                parent={ 'database_id': meals_page_id },
                                properties={
                                    'Restaurant': { 
                                        'relation': [{ 'id': restaurant_row_response['id'] }] 
                                    },
                                    'Meal Type': { 
                                        'select': { 'name': openai_response_json['Meal Type'] }
                                    },
                                    'Time': { 'date': { 'start': openai_response_json['Time'] } },
                                    'Method': {
                                        'select': { 'name': openai_response_json['Method'] }
                                    },
                                    'Source': {
                                        'select': { 'name': 'Email' }
                                    }
                                },
                            )

from streamlit_chat import message
def omnet_rag():
    if 'generated' not in st.session_state:
        st.session_state['generated'] = []

    if 'past' not in st.session_state:
        st.session_state['past'] = []
        
    if 'chat_status' not in st.session_state:
        st.session_state['chat_status'] = 'init'
        
    prompt = st.text_input(f"please ask: ", key="input")
    if st.button("Ask AI"):
        # if st.session_state['google_auth'] is None:
        #     message('please login with google first')
        # else:
        if st.session_state['chat_status'] == 'init':
            messages = []
            messages.append({"role": "user", "content": prompt})
            response = openai_client.chat_completion_request(messages).choices[0].message
            st.session_state.past.append(prompt)
            st.session_state.generated.append(response.content)
            st.session_state['chat_status'] = 'generated'
        elif st.session_state['chat_status'] == 'generated':
            messages = []
            messages.append({"role": "user", "content": prompt})
            response = openai_client.chat_completion_request(messages).choices[0].message
            st.session_state.past.append(prompt)
            st.session_state.generated.append(response.content)
        
    if st.session_state['generated']:
        # print("len(st.session_state['generated']) is ", len(st.session_state['generated']))

        for i in range(len(st.session_state['generated'])-1, -1, -1):
            message(st.session_state["generated"][i], key=str(i))
            message(st.session_state['past'][i], is_user=True, key=str(i) + '_user')
            
if __name__ == "__main__":
    oauth_google()
    oauth_notion()
    import_gmail()
    omnet_rag()
