import os

from celery import Celery
from celery.signals import setup_logging
from django.conf import settings

from .plugins import discover_plugins_modules


@setup_logging.connect
def setup_celery_logging(*_args, **_kwargs):
    """Skip default Celery logging configuration.

    Will rely on Django to set up the base root logger.
    """
    pass


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "saleor.settings")

app = Celery("saleor")

app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
app.autodiscover_tasks(lambda: discover_plugins_modules(settings.PLUGINS))
