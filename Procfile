release: python manage.py migrate --no-input
web: gunicorn --bind :$PORT --workers 4 --worker-class uvicorn.workers.UvicornWorker saleor.asgi:application
celeryworker: celery -A saleor --app=saleor.celeryconf:app worker --loglevel=info -E
