from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
# import email
import html2text
import base64
import pdb
from notion_client import Client
from datetime import datetime
from email.utils import parsedate_to_datetime

# read ./streamlit/secrets.toml
def read_toml(path):
    import toml
    with open(path, 'r') as f:
        config = toml.load(f)
    return config

class OmnetGmail:
    def __init__(self, config):
        self.config = config
        self.email_address = config['email_address']
        self.access_token = config['access_token']
        self.client_id = config['client_id']
        self.client_secret = config['client_secret']
        self.refresh_token = config['refresh_token']
        self.service = self.gmail_authenticate()
        self.h2t = html2text.HTML2Text()
        self.h2t.ignore_links = True
        self.h2t.ignore_images = True
        self.h2t.ignore_emphasis = True

    def gmail_authenticate(self):
        creds = Credentials.from_authorized_user_info({
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'refresh_token': self.refresh_token,
                'access_token': self.access_token
            },
            scopes=['https://www.googleapis.com/auth/gmail.readonly']
        )
        try:
            service = build('gmail', 'v1', credentials=creds)
            return service
        except Exception as e:
            print('An error occurred: %s' % e)
            return None

    def get_from_specific_email(self, email_address):
        try:
            results = self.service.users().messages().list(userId='me', q="from:{}".format(email_address)).execute()
            messages = results.get('messages', [])
            return messages
        except Exception as error:
            print('An error occurred: %s' % error)
            
    def get_from_id(self, email_id):
        try:
            message = self.service.users().messages().get(userId='me', id=email_id).execute()
            return message
        except Exception as e:
            print('An error occurred: %s' % e)
            return None
        
    def get_content_from_id(self, email_id):
        data = self.get_from_id(email_id)
        headers = data['payload']['headers']
        meta_data = {}
        for header in headers:
            name = header['name']
            if name.lower() == 'subject':
                meta_data['subject'] = header['value']
            if name.lower() == 'from':
                meta_data['sender'] = header['value']
            if name.lower() == 'to':
                meta_data['receiver'] = header['value']
            if name.lower() == 'date':
                meta_data['date'] = parsedate_to_datetime(header['value']).isoformat()
        
        if data['payload']['mimeType'] == 'text/html':
            html_content = base64.urlsafe_b64decode(data['payload']['body']['data']).decode('utf-8')
            markdown_content = self.h2t.handle(html_content)
            # markdown_content = html2text.html2text(html_content)
        elif data['payload']['mimeType'] == 'text/plain':
            markdown_content = data['payload']['body']['data']
        elif data['payload']['mimeType'] == 'multipart/alternative':
            for part in data['payload']['parts']:
                if part['mimeType'] == 'text/html':
                    html_content = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                    markdown_content = self.h2t.handle(html_content)
                    # markdown_content = html2text.html2text(html_content)
                elif part['mimeType'] == 'text/plain':
                    markdown_content = part['body']['data']
        else:
            markdown_content = "None"
        # pdb.set_trace()
        return meta_data, markdown_content
        
        # raw_email = data[0][1]
        # email_message = email.message_from_bytes(raw_email)

        # subject = email_message.get("Subject")
        # sender = email_message.get("From")
        # receiver = email_message.get("To")
        # date = email_message.get("Date")
        
        # meta_data = {
        #     "subject": subject,
        #     "sender": sender,
        #     "receiver": receiver,
        #     "date": date,
        # }

        # if email_message.is_multipart():
        #     for part in email_message.get_payload():
        #         if part.get_content_type() == 'text/html':
        #             html_content = part.get_payload()
        #             markdown_content = html2text.html2text(html_content)
        #             return meta_data, markdown_content
        # else:
        #     return meta_data, html2text.html2text(email_message.get_payload())

if __name__ == '__main__':
    # toml_file = read_toml('./.streamlit/secrets.toml')
    # config = {
    #     'client_id': toml_file['G_CLIENT_ID'],
    #     'client_secret': toml_file['G_CLIENT_SECRET'],
    #     'refresh_token': toml_file['G_REFRESH_TOKEN'],
    #     'email_address': 'guanqunhuang6@gmail.com',
    #     'access_token': toml_file['G_ACCESS_TOKEN'],
    # }
    # NOTION_ACCESS_TOKEN = toml_file['NOTION_ACCESS_TOKEN']
    # omnet_gmail = OmnetGmail(config)
    # messages = omnet_gmail.get_from_specific_email("no-reply@opentable.com")
    # notion_client_public = Client(auth=NOTION_ACCESS_TOKEN)
    # email_page_id = '763400cf-cada-4c2a-a75e-6588a260bf92'
    # for message in messages:
    #     meta_data, content = omnet_gmail.get_content_from_id(message['id'])
    #     print(meta_data['subject'])

    #     # notion_client_public.pages.create(
    #     #     parent={ 'database_id': email_page_id },
    #     #     properties={
    #     #         # 'Subject': { 'title': [{ 'type': 'text', 'text': { 'content': "aaa" }}] },
    #     #         'Sender': { 'email': meta_data['sender']},
    #     #         'Receiver': { 'email': meta_data['receiver']},
    #     #         'Date': { 'date': { 'start': meta_data['date'],}},
    #     #         'Email Content': { 'rich_text': [{ 'type': 'text', 'text': { 'content': content[:2000] }}] },
    #     #     },
    #     # )
    toml_file = read_toml('./.streamlit/secrets.toml')
    # pdb.set_trace()
    NOTION_USER_DATABASE_ID = toml_file["NOTION_USER_DATABASE_ID"]
    APP_DIRECTORY_DATABASE_ID = toml_file["APP_DIRECTORY_DATABASE_ID"]
    NOTION_PRIVATE_API_KEY = toml_file["NOTION_PRIVATE_API_KEY"]
    notion_private_client = Client(auth=NOTION_PRIVATE_API_KEY)
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
    
    config = {
        'client_id': toml_file['G_CLIENT_ID'],
        'client_secret': toml_file['G_CLIENT_SECRET'],
        'refresh_token': toml_file['G_REFRESH_TOKEN'],
        'email_address': 'guanqunhuang6@gmail.com',
        'access_token': toml_file['G_ACCESS_TOKEN'],
    }
    NOTION_ACCESS_TOKEN = toml_file['NOTION_ACCESS_TOKEN']
    omnet_gmail = OmnetGmail(config)
    for app_directory_result in app_directory_response["results"]:
        transactional_email = app_directory_result["properties"]["Transactional Email"]['email']
        key_words = app_directory_result["properties"]["Key String"]['rich_text'][0]['text']['content']
        print(transactional_email, key_words)
        if transactional_email != "expedia@eg.expedia.com":
            continue
        messages = omnet_gmail.get_from_specific_email(transactional_email)
        for message in messages:
            meta_data, content = omnet_gmail.get_content_from_id(message['id'])
            # pdb.set_trace()
            if key_words in meta_data['subject']:
                pdb.set_trace()