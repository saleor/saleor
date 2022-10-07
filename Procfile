release: python manage.py migrate --no-input
web: gunicorn --bind :$PORT --workers 4 --worker-class saleor.asgi.gunicorn_worker.UvicornWorker saleor.asgi:application
celeryworker: celery -A saleor --app=saleor.celeryconf:app worker --loglevel=info -E --concurrency ${CELERY_CONCURRENCY:-2}
