import mongo_db_logic

# simplify the  mongo_db_logic.UserData.objects call
user_data = mongo_db_logic.UserData.objects


def ask_intro_question(sms, conversation_id, sender_number, contact_method, incoming_message):


    intro_message = "Hello! I'm Ajira Bot, and I'm here to help you create a resume.\n"

    # Generate gpt response to ask for name
    question = "what is your name?"
    gpt_response = \
        sms \
            .gpt_logic \
            .generate_question_from_example(
            response=incoming_message,
            example_question=question
        )
    # Send the content to the user
    sms.send_message(conversation_id, intro_message + gpt_response)


def ask_detail(sms, conversation_id, sender_number, incoming_message, detail):
    validation_parameters = [detail]
    # Verify that the incoming content contains a name using the validate_response function
    validation_dict = sms.gpt_logic.validate_response(
        validation_parameters=validation_parameters,
        user_response=incoming_message
    )

    # If the response is valid, save the name to the database
    if bool(validation_dict['validation_status']):
        user_data(user_phone_number=sender_number).update_one(
            set__user_name=incoming_message
        )
        # Generate gpt response to ask for name
        question = "what is your email address?"
        gpt_response = \
            sms \
                .gpt_logic \
                .generate_question_from_example(
                response=incoming_message,
                example_question=question
            )
        # Send the content to the user
        sms.send_message(conversation_id, gpt_response)

    # If the validation failed, add the list of validation questions to the unasked questions list in the database
    elif bool(validation_dict['validation_status']) == False:
        user_data(user_phone_number=sender_number).update_one(
            push_all__unasked_questions=validation_dict['validation_questions']
        )
        # Take the first question from the list of validation questions and ask the user to try again
        sms.send_message(conversation_id, validation_dict['validation_questions'][0])

    else:
        # If the response is not valid, ask the user to try again
        sms.send_message(conversation_id, "I'm sorry, I didn't understand that. Please try again.")

