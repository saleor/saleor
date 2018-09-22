import os

import environ
from celery import Celery

env = environ.Env()
environ.Env.read_env(env_file=os.path.abspath(os.path.join(
    os.path.dirname(__file__), '..', '.env')))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'saleor.settings')

app = Celery('saleor', broker=env('CELERY_BROKER', default='amqp://'))
CELERY_TIMEZONE = env('CELERY_TIMEZONE', default='UTC')

app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
