web: gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app
worker: celery -A celery_worker_functions.celery_app worker --loglevel=info
