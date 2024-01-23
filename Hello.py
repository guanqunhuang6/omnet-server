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

from notion_db import NOTION_PRIVATE_API_KEY, NOTION_USER_DATABASE_ID
from notion_client import Client

notion_client = Client(auth=NOTION_PRIVATE_API_KEY)

st.set_page_config(
    page_title="omnet",
    page_icon=":robot:",
)



@st.cache_resource(experimental_allow_widgets=True) 
def get_manager():
    return stx.CookieManager()
cookie_manager = get_manager()

def oauth_google():
    st.title("Google Gmail Oauth2")
    CLIENT_ID = st.secrets["G_CLIENT_ID"]
    CLIENT_SECRET = st.secrets["G_CLIENT_SECRET"]
    AUTHORIZE_ENDPOINT = "https://accounts.google.com/o/oauth2/v2/auth"
    TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"
    REVOKE_ENDPOINT = "https://oauth2.googleapis.com/revoke"
    
    if not cookie_manager.get(cookie="google_auth") and "google_auth" not in st.session_state:
        # create a button to start the OAuth2 flow
        google_oauth2 = OAuth2Component(CLIENT_ID, CLIENT_SECRET, AUTHORIZE_ENDPOINT, TOKEN_ENDPOINT, TOKEN_ENDPOINT, REVOKE_ENDPOINT)
        google_result = google_oauth2.authorize_button(
            name="Continue with Google",
            icon="https://www.google.com.tw/favicon.ico",
            redirect_uri="https://omnet-server-aw0qwg29mdv.streamlit.app/",
            scope="openid email profile",
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
            print("+++++")
            cookie_manager.set("google_auth", st.session_state["google_auth"])
            print("=====")
            # cookie_manager.set("google_token", st.session_state["google_token"])
            st.rerun()
    else:
        # print(cookie_manager.get(cookie="google_auth"))
        st.write("You are logged in with google!")

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

    notion_client = NotionOAuth2(NOTION_OAUTH2_CLIENT_ID, NOTION_OAUTH2_CLIENT_SECRET)

    # create an OAuth2Component instance
    notion_oauth2 = OAuth2Component(
        # client_id=None,
        # client_secret=None,
        # authorize_endpoint=None,
        # token_endpoint=None,
        # refresh_token_endpoint=None,
        # revoke_token_endpoint=None,
        client=notion_client,
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
        
def import_gmail():
    pass

if __name__ == "__main__":
    oauth_google()
    oauth_notion()
