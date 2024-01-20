# Copyright (c) Streamlit Inc. (2018-2022) Snowflake Inc. (2022)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import streamlit as st
from streamlit.logger import get_logger
from httpx_oauth.oauth2 import BaseOAuth2
from typing import Any, Dict, List, Optional, Tuple, cast

LOGGER = get_logger(__name__)


# def run():
#     st.set_page_config(
#         page_title="Hello",
#         page_icon="👋",
#     )

#     st.write("# Welcome to Streamlit! 👋")

#     st.sidebar.success("Select a demo above.")

#     st.markdown(
#         """
#         Streamlit is an open-source app framework built specifically for
#         Machine Learning and Data Science projects.
#         **👈 Select a demo from the sidebar** to see some examples
#         of what Streamlit can do!
#         ### Want to learn more?
#         - Check out [streamlit.io](https://streamlit.io)
#         - Jump into our [documentation](https://docs.streamlit.io)
#         - Ask a question in our [community
#           forums](https://discuss.streamlit.io)
#         ### See more complex demos
#         - Use a neural net to [analyze the Udacity Self-driving Car Image
#           Dataset](https://github.com/streamlit/demo-self-driving)
#         - Explore a [New York City rideshare dataset](https://github.com/streamlit/demo-uber-nyc-pickups)
#     """
#     )
import streamlit as st
from streamlit_oauth import OAuth2Component
import os
import base64
import json

def oauth_google():
    st.set_page_config(
        page_title="omnet",
        page_icon=":robot:",
    )
    st.title("Google Gmail Oauth2")
    # st.write("This example shows how to use the OAuth2 component to authenticate with Google Gmail API.")
    CLIENT_ID = st.secrets["G_CLIENT_ID"]
    CLIENT_SECRET = st.secrets["G_CLIENT_SECRET"]
    AUTHORIZE_ENDPOINT = "https://accounts.google.com/o/oauth2/v2/auth"
    TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"
    REVOKE_ENDPOINT = "https://oauth2.googleapis.com/revoke"
    
    if "auth" not in st.session_state:
        # create a button to start the OAuth2 flow
        oauth2 = OAuth2Component(CLIENT_ID, CLIENT_SECRET, AUTHORIZE_ENDPOINT, TOKEN_ENDPOINT, TOKEN_ENDPOINT, REVOKE_ENDPOINT)
        result = oauth2.authorize_button(
            name="Continue with Google",
            icon="https://www.google.com.tw/favicon.ico",
            # redirect_uri="http://192.168.1.184:8501",
            # redirect_uri="http://localhost:8501",
            redirect_uri="https://omnet-server-aw0qwg29mdv.streamlit.app/",
            scope="openid email profile",
            key="google",
            extras_params={"prompt": "consent", "access_type": "offline"},
            use_container_width=True,
        )

        if result:
            st.write(result)
            # decode the id_token jwt and get the user's email address
            id_token = result["token"]["id_token"]
            # verify the signature is an optional step for security
            payload = id_token.split(".")[1]
            # add padding to the payload if needed
            payload += "=" * (-len(payload) % 4)
            payload = json.loads(base64.b64decode(payload))
            email = payload["email"]
            st.session_state["auth"] = email
            st.session_state["token"] = result["token"]
            st.rerun()
    else:
        st.write("You are logged in with google!")

def oauth_notion():
    NOTION_OAUTH2_CLIENT_ID = st.secrets["NOTION_OAUTH2_CLIENT_ID"]
    NOTION_OAUTH2_CLIENT_SECRET = st.secrets["NOTION_OAUTH2_CLIENT_SECRET"]
    NOTION_OAUTH2_AUTHORIZATION_URL = "https://api.notion.com/v1/oauth/authorize"
    # NOTION_OAUTH2_AUTHORIZATION_URL = "https://api.notion.com/v1/oauth/authorize?client_id=6c404a6b-7239-4c4d-b0b0-419109232c69&response_type=code&owner=user&redirect_uri=https%3A%2F%2Fomnet.life%2Fnotion%2Fcallback"
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
    oauth2 = OAuth2Component(
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
        result = oauth2.authorize_button(
            name="Login with Notion",
            icon="https://www.notion.so/images/favicon.ico",
            # redirect_uri="http://localhost:8501",
            redirect_uri="https://omnet-server-aw0qwg29mdv.streamlit.app/",
            scope="user",
            key="notion",
            extras_params={"owner": "user"},
            use_container_width=True,
        )

        if result:
            st.session_state["notion_token"] = result
            st.rerun()
    else:
        st.write("You are logged in with notion!")
        # st.write(st.session_state["notion_token"])
        # st.button("Logout")
        # del st.session_state["notion_token"]
        
if __name__ == "__main__":
    oauth_google()
    oauth_notion()
