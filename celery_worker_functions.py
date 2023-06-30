from celery_app import celery_app
import mongo_db_logic as db
import logging

from aws_logic import create_resume_document
from short_url_logic import shorten_url
from sms_logic import SMSLogic

user_data = db.UserData.objects
sms = SMSLogic()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@celery_app.task(name='celery_worker_functions.generate_resume')
def generate_resume(conversation_id, sender_number, message_list):
    """Generate a resume and send a download link to the user"""
    user = user_data(conversation_id=conversation_id).first()

    logger.info("generate_resume main.py")
    user_name, resume_file_link = create_resume_document(
        user=user,
        message_list=message_list,
        conversation_id=conversation_id,
        sender_number=sender_number
    )

    # shorten the resume file link
    short_url = shorten_url(resume_file_link)

    # create a message to send to the user with a link to download their resume
    link_message_text = f"Hi {user_name}, your resume is ready. " \
                        f"Click the link below to download it: {short_url}"

    # send a message to the user with a link to download their resume
    sms.send_message(
        message=link_message_text,
        conversation_id=conversation_id,
        phone_number=sender_number
    )

    # save message to database
    db.save_message_to_database(
        conversation_id=conversation_id,
        content=link_message_text,
        role='assistant',
        phone_number=sender_number,
    )

    # update the user object to show that the resume has been generated
    user.update(is_resume_generated=True)
