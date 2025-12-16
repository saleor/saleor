import logging
import os

from celery import Celery
from celery.signals import setup_logging, worker_process_init
from django.conf import settings

from .core.telemetry import initialize_telemetry
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


@worker_process_init.connect(weak=False)
def init_celery_telemetry(*args, **kwargs):
    initialize_telemetry()


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "saleor.settings")

app = Celery("saleor", task_cls="saleor.core.tasks:RestrictWriterDBTask")

app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
app.autodiscover_tasks(
    packages=[
        "saleor.app.migrations.tasks",
    ],
    related_name="saleor3_23",
)
app.autodiscover_tasks(
    packages=[
        "saleor.order.migrations.tasks",
        "saleor.account.migrations.tasks",
        "saleor.attribute.migrations.tasks",
        "saleor.channel.migrations.tasks",
    ],
    related_name="saleor3_22",
)
app.autodiscover_tasks(
    packages=[
        "saleor.checkout.migrations.tasks",
        "saleor.order.migrations.tasks",
    ],
    related_name="saleor3_20",
)
app.autodiscover_tasks(lambda: discover_plugins_modules(settings.PLUGINS))
app.autodiscover_tasks(related_name="search_tasks")
