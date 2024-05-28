import logging
import os

from celery import Celery, Task
from celery.signals import setup_logging
from django.conf import settings
from django.db import connections

from .plugins import discover_plugins_modules

CELERY_LOGGER_NAME = "celery"


class RestrictWriterDBTask(Task):
    """Task that restricts write operations to the writer database.

    Depending on the configuration, this task logs warning or raises an error when it
    detects a writer DB query that is not wrapped in `allow_writer` context manager.
    """

    def __call__(self, *args, **kwargs):
        from saleor.core.db.connection import _restrict_writer

        # TODO: Make the wrapper configurable to either log a warning or raise an error
        with connections[settings.DATABASE_CONNECTION_DEFAULT_NAME].execute_wrapper(
            _restrict_writer
        ):
            return super().__call__(*args, **kwargs)


@setup_logging.connect
def setup_celery_logging(loglevel=None, **kwargs):
    """Skip default Celery logging configuration.

    Will rely on Django to set up the base root logger.
    Celery loglevel will be set if provided as Celery command argument.
    """
    if loglevel:
        logging.getLogger(CELERY_LOGGER_NAME).setLevel(loglevel)


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "saleor.settings")

app = Celery("saleor", task_cls=RestrictWriterDBTask)

app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
app.autodiscover_tasks(lambda: discover_plugins_modules(settings.PLUGINS))  # type: ignore[misc] # circular import # noqa: E501
app.autodiscover_tasks(related_name="search_tasks")
