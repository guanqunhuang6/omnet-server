from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import pdb
class OmnetGmail:
    def __init__(self, config):
        self.config = config
        self.email_address = config['email_address']
        self.access_token = config['access_token']
        self.service = self.gmail_authenticate()

    def gmail_authenticate(self):
        creds = Credentials.from_authorized_user_info({'access_token': self.access_token})
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

    # rest of your code...

if __name__ == '__main__':
    config = {
        'email_address': 'guanqunhuang6@gmail.com',
        'access_token': 'ya29.a0AfB_byAEjNczuDJfHDYy7tV5YbBnENAdTYRsVCpBsnYfCH3V59qa1A71WnQJ-lpl-WbMnbQw8rd4AYuc72w_zpMQRXzMaAu-1XoikPVzwTcnhSR1pOU2s6Z6NopX3jjQhr-_afa0Qa8uwSwkoJcnbwdkGp1ARAVCNUuaaCgYKATQSARESFQHGX2Mi6TUTM3n-kh7R9cIc0-nL1Q0171'
    }
    omnet_gmail = OmnetGmail(config)
    messages = omnet_gmail.get_from_specific_email("no-reply@opentable.com")
    pdb.set_trace()