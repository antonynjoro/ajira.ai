import os
import random
import string

import certifi
from mongoengine import connect, Document, StringField, DateTimeField, IntField, ListField, DictField, \
    EmbeddedDocumentField, EmbeddedDocument, BooleanField, register_connection
import datetime


# Connect to MongoDB
connect(
    'Ajira_db',
    host=os.environ['MONGO_CONNECTION_STRING'],
    tls=True,
    tlsCAFile=certifi.where()
)
def generate_random_user_id():
    """Generate a random 5 character user id from Upper Case letters and numbers"""
    user_id = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(6))
    return user_id


# Message class that is embedded in the UserData class
class Message(EmbeddedDocument):
    """A content sent to or from the user"""
    role = StringField(required=True, choices=['user', 'assistant'])
    content = StringField(required=True)


class Resume(EmbeddedDocument):
    """A resume generated by GPT-3"""
    resume_content = StringField(required=True)
    resume_created_at = DateTimeField(default=datetime.datetime.utcnow)
    resume_file_link = StringField()


class UserInformationSummary(EmbeddedDocument):
    """A summary of the user's information provided to the chatbot"""
    information_summary = StringField(required=True)
    created_at = DateTimeField(default=datetime.datetime.utcnow)


class FollowupQuestionSet(EmbeddedDocument):
    """A set of followup questions generated by GPT-3 based on an incomplete response by the user"""
    bot_question = StringField(required=True)
    user_response = StringField(required=True)
    unasked_questions = ListField(StringField())
    asked_questions = ListField(StringField())


class UserData(Document):
    """A conversation between a user and the chatbot"""

    # Define the fields for the UserData class
    conversation_id = StringField(required=True)
    user_phone_number = StringField(required=True, unique=True, max_length=20, min_length=10, regex=r'^\+?1?\d{9,15}$',
                                    error_message='Phone number must be entered in the format: \'+999999999\'. Up to 15 digits allowed.')
    user_status = StringField(required=True, choices=['active', 'suspended'], default='active')
    contact_method = StringField(required=True, error_message='Contact method must be either \'SMS\' or \'Whatsapp\'')
    user_id = StringField(default=generate_random_user_id)
    is_resume_generated = BooleanField(default=False)
    user_name = StringField()
    user_email = StringField()
    user_address = StringField()
    user_city = StringField()
    user_state = StringField()
    user_zip = StringField()
    user_country = StringField()
    user_work_experience = ListField(DictField())
    user_education = ListField(DictField())
    user_skills = ListField(DictField())
    user_resumes = ListField(EmbeddedDocumentField(Resume))
    created_at = DateTimeField(default=datetime.datetime.utcnow)
    updated_at = DateTimeField(default=datetime.datetime.utcnow)
    messages = ListField(EmbeddedDocumentField(Message))
    user_information_summary = EmbeddedDocumentField(UserInformationSummary)
    followup_questions = ListField(EmbeddedDocumentField(FollowupQuestionSet))

    # Define the indexes for the UserData class
    meta = {'collection': 'user_data', 'db_alias': 'default'}


    def save(self, *args, **kwargs):
        self.updated_at = datetime.datetime.utcnow()
        super(UserData, self).save(*args, **kwargs)


def create_user_data(conversation_id, phone_number, contact_method='SMS'):
    """Create a new user data object and save it to the database"""
    user_data = UserData(conversation_id=conversation_id, user_phone_number=phone_number,
                         contact_method=contact_method)

    user_data.save()


def save_message_to_database(conversation_id, content, role, phone_number):
    """Save a content to the database"""
    # if no user data exists for this conversation, create a new user data object
    if not UserData.objects(conversation_id=conversation_id).first():
        create_user_data(conversation_id=conversation_id, phone_number=phone_number)

    # create a new content object using the Messages class schema
    new_message = Message(
        content=content,
        role=role
    )
    # append the new content to the list of messages
    user_data = UserData.objects(conversation_id=conversation_id).first()
    user_data.messages.append(new_message)
    user_data.save()

    return


def save_summary_to_database(conversation_id, summary):
    """Save a summary to the database

    Params:
        conversation_id: the id of the conversation
        summary: a summary of the user's information provided to the chatbot

    Returns:
        the summary of the user's information provided to the chatbot
    """
    # create a new summary object using the UserInformationSummary class schema
    new_summary = UserInformationSummary(
        information_summary=summary
    )
    # append the new summary to the list of summaries
    user_data = UserData.objects(conversation_id=conversation_id).first()
    user_data.user_information_summary = new_summary
    user_data.save()

    return user_data.user_information_summary.information_summary


def save_resume_to_database(conversation_id, resume_content, resume_file_link):
    """Save a resume to the database and return the id of the resume"""
    # create a new resume object using the Resume class schema
    new_resume = Resume(
        resume_content=resume_content,
        resume_file_link=resume_file_link
    )
    # append the new resume to the list of resumes
    user_data = UserData.objects(conversation_id=conversation_id).first()
    user_data.user_resumes.append(new_resume)
    user_data.save()

    # return the id of the new resume
    return


def save_user_name_to_database(conversation_id, user_name):
    """Save a user's name to the database"""
    user_data = UserData.objects(conversation_id=conversation_id).first()
    user_data.user_name = user_name
    user_data.save()

    return
