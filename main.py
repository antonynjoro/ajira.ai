"""SMS chatbot that helps create a resume"""
import time

from sms_logic import SMSLogic
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import mangum
import mongo_db_logic
import gpt_logic
import docx
from pydantic import BaseModel


class Message(BaseModel):
    """Message model"""
    MessagingServiceSid: str
    EventType: str
    Attributes: str
    DateCreated: str
    Index: int
    ChatServiceSid: str
    MessageSid: str
    AccountSid: str
    Source: str
    RetryCount: int
    Author: str
    ParticipantSid: str
    Body: str
    ConversationSid: str


# simplify the  mongo_db_logic.UserData.objects call
user_data = mongo_db_logic.UserData.objects

app = FastAPI()
handler = mangum.Mangum(app)


@app.get('/')
async def root():
    return {'message': 'Hello World'}


@app.post('/sms', response_class=JSONResponse)
async def receive_sms(request: Request):
    """Handle incoming SMS messages sent to your Twilio phone number"""
    sms = SMSLogic()
    gpt = gpt_logic.GPTLogic()
    print('received sms')

    form_data = await request.form()
    message_data = {key: str(value) for key, value in form_data.items()}
    message = Message(**message_data)

    # print the incoming response
    print(message)

    # print the incoming message
    incoming_message = message.Body
    print(incoming_message)
    conversation_id = message.ConversationSid
    print(conversation_id)
    sender_number = message.Author
    print(sender_number)
    contact_method = message.Source
    print(contact_method)
    created_at = message.DateCreated
    print(created_at)

    # If the content's conversation ID is not in the database, create a new user data object
    if not user_data(user_phone_number=sender_number).first():
        print("No user found with that conversation ID")
        mongo_db_logic.create_user_data(conversation_id=conversation_id, phone_number=sender_number,
                                        contact_method=contact_method)

    # Save the incoming message to the database
    mongo_db_logic.save_message_to_database(
        conversation_id=conversation_id,
        content=incoming_message,
        role='user',
        phone_number=sender_number,
    )

    if user_data(conversation_id=conversation_id).first().is_resume_generated == False:

        # retrieve the messages list from the database
        message_objects = user_data(conversation_id=conversation_id).first().messages

        message_list = [message.to_mongo() for message in message_objects]

        # get the content from the gpt chat method
        gpt_response_string = gpt.chat(message_list)['content']

        # end state if the bot response contains the string '<END>'
        if '<END>' in gpt_response_string:
            # add the gpt response to the database
            mongo_db_logic.save_message_to_database(
                conversation_id=conversation_id,
                content=gpt_response_string,
                role='assistant',
                phone_number=sender_number,
            )

            # remove the <END> string from the response
            edited_gpt_response_string = gpt_response_string.replace('<END>', 'Malisia')
            sms.send_message(
                message=edited_gpt_response_string,
                conversation_id=conversation_id,
                phone_number=sender_number
            )

            # make the resume generated field in the database true
            user_data(conversation_id=conversation_id).first().update(is_resume_generated=True)

            # create a summary of the key information provided by the user  save it to the database in the UserInformationSummary field
            mongo_db_logic.save_summary_to_database(
                summary=gpt.summarize_messages(messages=message_list),
                conversation_id=conversation_id
            )

            # pull the summary from the database
            user_information_summary = user_data(
                conversation_id=conversation_id).first().user_information_summary.information_summary

            # Use the summary to generate a full resume and save it to the database
            resume_content = gpt.generate_resume(
                resume_inputs=user_information_summary,
                user_phone_number=sender_number
            )

            # Save the resume to the database
            mongo_db_logic.save_resume_to_database(
                conversation_id=conversation_id,
                resume_content=resume_content,
            )

            # create a .docx file with the resume content
            document = docx.Document()
            document.add_paragraph(resume_content)

            # save the document in the aws s3 bucket





        # main chat loop until the user provides the string '<END>'
        else:
            # add the gpt response to the database
            mongo_db_logic.save_message_to_database(
                conversation_id=conversation_id,
                content=gpt_response_string,
                role='assistant',
                phone_number=sender_number,
            )

            # send the gpt response to the user via sms
            sms.send_message(
                message=gpt_response_string,
                conversation_id=conversation_id,
                phone_number=sender_number
            )

    elif user_data(conversation_id=conversation_id).first().is_resume_generated == True:
        # send a message to the user asking if they have any corrections to the resume
        sms.send_message(
            message="Would you like to make any corrections to your resume?",
            conversation_id=conversation_id,
            phone_number=sender_number
        )

        # TODO: send the user a message with a link to download their resume from the database then send a message
        #       asking if they have any corrections to the resume. If they do, loop through asking if there is anyting
        #       else they would like to change. If they don't, send a message saying that the resume is being
        #       corrected and will be sent to them soon.

    return {'message:': 'success'}
