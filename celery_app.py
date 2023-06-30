import os
from celery import Celery

from main import generate_resume

BROKER_URL = os.environ.get('CLOUDAMQP_URL', 'pyamqp://guest@localhost//') 
celery_app = Celery('tasks', broker=BROKER_URL)

# If your tasks are not auto-discovered, you might need to manually register them:
celery_app.tasks.register(generate_resume)