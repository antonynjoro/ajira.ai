"""SMS chatbot that helps create a resume"""


from sms_logic import SMSLogic
from flask import Flask, request
import mongo_db_logic
import bot_logic as bot

# simplify the  mongo_db_logic.UserData.objects call
user_data = mongo_db_logic.UserData.objects

app = Flask(__name__)


@app.route('/sms', methods=['POST'])
def receive_sms():
    """Handle incoming SMS messages sent to your Twilio phone number"""
    sms = SMSLogic()
    print('received sms')
    print(request.form)
    incoming_message = request.form['Body']
    print(incoming_message)
    conversation_id = request.form['ConversationSid']
    print(conversation_id)
    sender_number = request.form['Author']
    print(sender_number)
    contact_method = request.form['Source']
    print(contact_method)
    created_at = request.form['DateCreated']
    print(created_at)

    # If the message's conversation ID is not in the database, create a new user data object
    if not user_data(user_phone_number=sender_number).first():
        print("No user found with that conversation ID")
        mongo_db_logic.create_user_data(conversation_id, sender_number, contact_method)
        # Save the message to the database
        mongo_db_logic.save_message_to_database(
            conversation_id=conversation_id,
            message=incoming_message,
            role='User',
            direction='inbound'
        )

        bot.ask_intro_question(
            sms=sms,
            sender_number=sender_number,
            conversation_id=conversation_id,
            contact_method=contact_method,
            incoming_message=incoming_message,

        )

    # if there is an unasked question in the user data object, ask it
    elif user_data(user_phone_number=sender_number).first().followup_questions and \
            user_data(user_phone_number=sender_number).first().followup_questions[0].unasked_questions:
        # your code here
        # Get the next question to ask the user
        question = user_data(user_phone_number=sender_number).first().unasked_questions[0]
        # Send the message to the user
        sms.send_message(conversation_id, question)
        # remove the question from the list of unasked questions and add it to the list of asked questions
        user_data(user_phone_number=sender_number).update_one(
            pop__unasked_questions=question,
            push__asked_questions=question
        )

    # If the user data object does not have a name, ask for their name
    elif not user_data(user_phone_number=sender_number).first().user_name:
        bot.ask_detail(
            sms=sms,
            conversation_id=conversation_id,
            sender_number=sender_number,
            incoming_message=incoming_message,
            detail='name'
        )

    # If the user data object does not have an email address, ask for their email address
    elif not user_data(user_phone_number=sender_number).first().user_email:
        bot.ask_detail(
            sms=sms,
            conversation_id=conversation_id,
            sender_number=sender_number,
            incoming_message=incoming_message,
            detail='email_address'
        )

    # If the user data object does not have an address, ask for their address
    elif not user_data(user_phone_number=sender_number).first().user_address:
        bot.ask_detail(
            sms=sms,
            conversation_id=conversation_id,
            sender_number=sender_number,
            incoming_message=incoming_message,
            detail='address'
        )

    # If the user data object does not have a zip code, ask for their zip code
    elif not user_data(user_phone_number=sender_number).first().user_zip_code:
        bot.ask_detail(
            sms=sms,
            conversation_id=conversation_id,
            sender_number=sender_number,
            incoming_message=incoming_message,
            detail='zip code'
        )

    # If the user data object does not have a State, ask for their State
    elif not user_data(user_phone_number=sender_number).first().user_state:
        bot.ask_detail(
            sms=sms,
            conversation_id=conversation_id,
            sender_number=sender_number,
            incoming_message=incoming_message,
            detail='state'
        )

    return '', 204


if __name__ == '__main__':
    app.run()
