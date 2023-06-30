import os
from celery import Celery

BROKER_URL = os.environ.get('CLOUDAMQP_URL', 'pyamqp://guest@localhost//') 
celery_app = Celery('tasks', broker=BROKER_URL)
