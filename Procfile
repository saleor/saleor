release: python manage.py migrate --no-input
web: uwsgi dastkari/wsgi/uwsgi.ini
celeryworker: celery worker -A dastkari.celeryconf:app --loglevel=info -E
