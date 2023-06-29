import logging
from datetime import datetime
from os import remove, environ

import boto3
import docx

import gpt_logic
import mongo_db_logic as db

s3 = boto3.client('s3', aws_access_key_id=environ['AWS_ACCESS_KEY_ID'], aws_secret_access_key=environ['AWS_SECRET_ACCESS_KEY'])


def create_presigned_url(bucket_name, object_name, expiration=86400):
    """Generate a presigned URL to share an S3 object

    :param bucket_name: string
    :param object_name: string
    :param expiration: Time in seconds for the presigned URL to remain valid
    :return: Presigned URL as string. If error, returns None.
    """

    # Generate a presigned URL for the S3 object

    response = s3.generate_presigned_url('get_object',
                                         Params={'Bucket': bucket_name,
                                                 'Key': object_name},
                                         ExpiresIn=expiration
                                         )

    # The response contains the presigned URL
    return response


def create_resume_document(user, message_list, conversation_id, sender_number) -> tuple:
    """Create a resume document and save it to the aws s3 bucket


    :param user: user object
    :param message_list: list of messages
    :param conversation_id: conversation id
    :param sender_number: user phone number
    :return: user's name and resume file link
    """
    logging.info("create_resume_document aws_logic.py")
    # import the necessary modules
    gpt = gpt_logic.GPTLogic()

    # create a summary of the key information provided by the user  save it to the database in the
    # UserInformationSummary field
    logging.info(f"Message list to be summarized: {message_list}")

    user_information_summary = db.save_summary_to_database(
        summary=gpt.summarize_messages(messages=message_list),
        conversation_id=conversation_id
    )
    logging.info(f"User information summary: {user_information_summary}")

    # Use the summary to generate a full resume and save it to the database
    resume_content = gpt.generate_resume(
        resume_inputs=user_information_summary,
        user_phone_number=sender_number
    )
    logging.info(f"Resume content: {resume_content}")

    # Get the user's name by feeding the summary to the gpt model and save it to the database
    user_name = gpt.get_user_name(user_information_summary)
    db.save_user_name_to_database(
        conversation_id=conversation_id,
        user_name=user_name
    )
    logging.info(f"User name: {user_name}")

    # date in the format of 2021-08-01
    date = str(datetime.now().date())

    file_name = f'{user_name} Resume {date}.docx'

    # create a .docx file with the resume content
    document = docx.Document()
    document.add_paragraph(resume_content)
    document.save(file_name)

    # save the document in the aws s3 bucket
    bucket_name = 'ajira-resume-generator'

    # upload the resume to the s3 bucket
    with open(file_name, 'rb') as document:
        s3.upload_fileobj(
            document,
            bucket_name,
            file_name,
        )

    # get the presigned url to the resume file
    presigned_resume_file_link = create_presigned_url(bucket_name=bucket_name, object_name=file_name)

    # Save the resume to the database
    db.save_resume_to_database(
        conversation_id=conversation_id,
        resume_content=resume_content,
        resume_file_link=presigned_resume_file_link
    )

    # delete the file from the local machine
    remove(file_name)

    return user_name, presigned_resume_file_link
