import os
from celery import Celery
from celery_worker_functions import generate_resume



BROKER_URL = os.environ.get('CLOUDAMQP_URL', 'pyamqp://guest@localhost//')
celery_app = Celery('tasks', broker=BROKER_URL)



# Register tasks
celery_app.register_task(generate_resume)

