web: gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app
worker: celery -A celery_app.celery_app worker --loglevel=info

