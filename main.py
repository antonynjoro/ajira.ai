"""SMS chatbot that helps create a resume using GPT-3 and Twilio Conversations API"""
import logging
from sms_logic import SMSLogic
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import mongo_db_logic as db
import gpt_logic
from pydantic import BaseModel, Field
from short_url_logic import shorten_url

app = FastAPI()
user_data = db.UserData.objects
sms = SMSLogic()
gpt = gpt_logic.GPTLogic()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Message(BaseModel):
    """Message model"""
    MessageSid: str = Field(..., description="Twilio message id")
    AccountSid: str = Field(..., description="Twilio account id")
    Body: str = Field(..., description="Message content")
    ConversationSid: str = Field(..., description="Twilio conversation id")
    Author: str = Field(..., description="Message author")
    Source: str = Field(..., description="Message source, either 'sms' or 'whatsapp'")


def find_or_create_user(conversation_id, sender_number, source):
    """Find or create a user in the database"""
    user = user_data(conversation_id=conversation_id).first()
    if not user:
        logging.info("Creating new user data object")
        db.create_user_data(
            conversation_id=conversation_id,
            phone_number=sender_number,
            contact_method=source
        )
        user = user_data(conversation_id=conversation_id).first()
    else:
        logging.info("User already exists")
    return user



@app.get('/')
async def root():
    return {'message': 'Hello World'}


@app.post('/sms', response_class=JSONResponse)
async def receive_sms(request: Request):
    """Handle incoming SMS messages sent to your Twilio phone number"""

    form_data = await request.form()

    # log the incoming message
    logging.info(f"Incoming message: {form_data}")

    message_data = {key: str(value) for key, value in form_data.items()}
    message = Message(**message_data)

    logging.info(f"Incoming message: {message}")

    incoming_message = message.Body
    conversation_id = message.ConversationSid
    sender_number = message.Author

    user = find_or_create_user(conversation_id, sender_number, message.Source)

    # Save the incoming message to the database
    db.save_message_to_database(
        conversation_id=conversation_id,
        content=incoming_message,
        role='user',
        phone_number=sender_number,
    )

    # Pull the user object from the database again to get the latest data
    user = user_data(conversation_id=conversation_id).first()

    # Check if the system has already generated a resume for the user
    if not user.is_resume_generated:
        logging.info("Resume not generated")

        message_objects = user.messages
        message_list = [dict(message.to_mongo()) for message in message_objects]

        # Get the response from the GPT-3 chatbot
        gpt_response_string = gpt.chat(message_list)['content']

        db.save_message_to_database(
            conversation_id=conversation_id,
            content=gpt_response_string,
            role='assistant',
            phone_number=sender_number,
        )

        if '<END>' in gpt_response_string:
            logging.info("End state reached, generating resume...")
            message_list = [dict(message.to_mongo()) for message in message_objects]
            logging.info("Message list being exported from main.py at if '<END>': ", message_list)
            generate_resume.delay(conversation_id, sender_number, message_list)
        else:
            logging.info("Main chat loop. Sending response to user...")
            sms.send_message(
                message=gpt_response_string,
                conversation_id=conversation_id,
                phone_number=sender_number
            )

    elif user.is_resume_generated:
        logging.info("Resume already generated")
        sms.send_message(
            message="Would you like to make any corrections to your resume?",
            conversation_id=conversation_id,
            phone_number=sender_number
        )

    return {'message': 'success'}

# success
