"""Twilio SMS logic to send and receive messages with the help of GPTLogic and store them in MongoDB"""

import os
from twilio.rest import Client
from flask import Flask, request

import mongo_db_logic as db
import gpt_logic

app = Flask(__name__)








class SMSLogic:
    """Twilio SMS logic to send and receive messages with the help of GPTLogic and store them in MongoDB"""

    def __init__(self):
        self.account_sid = os.environ['TWILIO_ACCOUNT_SID']
        self.auth_token = os.environ['TWILIO_AUTH_TOKEN']
        self.client = Client(self.account_sid, self.auth_token)
        self.gpt_logic = gpt_logic.GPTLogic()
        self.preliminary_information_to_collect = ['name', 'email', 'address']



    def send_message(self, conversation_id, message):
        """Send a message to the user and save it to their user data in the database"""
        self.client.conversations \
            .v1 \
            .conversations(conversation_id) \
            .messages \
            .create(body=message)

        db.save_message_to_database(
            conversation_id=conversation_id,
            message=message,
            sender='Ajira_bot',
            direction='outbound',
        )

        return

    def get_messages(self, conversation_id):
        """Get all the messages from the user"""
        messages = self.client.conversations \
            .v1 \
            .conversations(conversation_id) \
            .messages \
            .list()

        return messages

    def get_user_data(self, conversation_id):
        """Get the user data from the database"""
        user_data = db.UserData.objects(conversation_id=conversation_id).first()
        return user_data

