release: python manage.py migrate --no-input
web: gunicorn --bind :$PORT --workers 2 --worker-class uvicorn.workers.UvicornWorker saleor.asgi:application
celeryworker: celery worker --app=saleor.celery_app --loglevel=info
