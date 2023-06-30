import logging
import os

from celery import Celery
from celery.signals import setup_logging
from django.conf import settings

from .plugins import discover_plugins_modules

CELERY_LOGGER_NAME = "celery"


@setup_logging.connect
def setup_celery_logging(loglevel=None, **kwargs):
    """Skip default Celery logging configuration.

    Will rely on Django to set up the base root logger.
    Celery loglevel will be set if provided as Celery command argument.
    """
    if loglevel:
        logging.getLogger(CELERY_LOGGER_NAME).setLevel(loglevel)


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "saleor.settings")

app = Celery("saleor")

app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
app.autodiscover_tasks(
    packages=[
        "saleor.order.migrations.tasks",
    ],
    related_name="saleor3_15",
)
app.autodiscover_tasks(lambda: discover_plugins_modules(settings.PLUGINS))  # type: ignore[misc] # circular import # noqa: E501
app.autodiscover_tasks(related_name="search_tasks")
