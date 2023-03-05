# Download the helper library from https://www.twilio.com/docs/python/install
import os
from twilio.rest import Client

CONVERSATION_ID = 'CH37d136b57a0a480791042366eaf4b0bc'
# ISc75addcee3a9454285098a282328e289
# MB6e8a66698e7d4ae192cadf35dd7dde5d

# Find your Account SID and Auth Token at twilio.com/console
# and set the environment variables. See http://twil.io/secure
account_sid = os.environ['TWILIO_ACCOUNT_SID']
auth_token = os.environ['TWILIO_AUTH_TOKEN']
client = Client(account_sid, auth_token)

messages = client.conversations \
                 .v1 \
                 .conversations(CONVERSATION_ID) \
                 .messages \
                 .list()


for record in messages:
    print(record.author, record.body)