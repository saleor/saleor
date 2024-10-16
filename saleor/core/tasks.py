import logging

from celery import Task
from celery.utils.log import get_task_logger
from django.conf import settings
from django.core.files.storage import default_storage
from django.db import connections
from django.db.models import Exists, OuterRef
from django.utils import timezone

from ..celeryconf import app
from ..core.db.connection import allow_writer
from . import private_storage
from .models import EventDelivery, EventPayload

task_logger: logging.Logger = get_task_logger(__name__)


class RestrictWriterDBTask(Task):
    """Celery task that checks usage of unrestricted queries to the writer database.

    A base class for Celery tasks that protects from inexplicit usages of DB queries
    to the writer DB. Depending on the `CELERY_RESTRICT_WRITER_METHOD` setting, the task
    will either log a warning (suitable for production) or raise an exception (suitable
    for tests).

    The `CELERY_RESTRICT_WRITER_METHOD` setting should point to one of the following:
    - `saleor.core.db.connection.log_writer_usage` - logs a warning
    - `saleor.core.db.connection.restrict_writer` - raises an exception
    """

    def __call__(self, *args, **kwargs):
        from django.utils.module_loading import import_string

        func_path = settings.CELERY_RESTRICT_WRITER_METHOD
        if not func_path:
            return None

        try:
            wrapper_fun = import_string(func_path)
        except ImportError:
            task_logger.error(
                "Could not import the function %s. Check if the path is correct.",
                func_path,
            )
            return super().__call__(*args, **kwargs)

        with connections[settings.DATABASE_CONNECTION_DEFAULT_NAME].execute_wrapper(
            wrapper_fun
        ):
            return super().__call__(*args, **kwargs)


# Batch size was tested on db with 1mln payloads and deliveries, each delivery
# had multiple attempts. One task took less than 0,5 second, memory usage didn't raise
# more than 100 MB.
BATCH_SIZE = 1000


@app.task
def delete_from_storage_task(path):
    default_storage.delete(path)


@app.task
def delete_event_payloads_task(expiration_date=None):
    expiration_date = (
        expiration_date
        or timezone.now() + settings.EVENT_PAYLOAD_DELETE_TASK_TIME_LIMIT
    )
    delete_period = timezone.now() - settings.EVENT_PAYLOAD_DELETE_PERIOD
    valid_deliveries = EventDelivery.objects.filter(created_at__gt=delete_period)
    payloads_to_delete = (
        EventPayload.objects.using(settings.DATABASE_CONNECTION_REPLICA_NAME)
        .filter(~Exists(valid_deliveries.filter(payload_id=OuterRef("id"))))
        .order_by("-pk")
    )
    ids = list(payloads_to_delete.values_list("pk", flat=True)[:BATCH_SIZE])
    if ids:
        if expiration_date > timezone.now():
            qs = EventPayload.objects.filter(pk__in=ids)
            files_to_delete = [
                event_payload.payload_file.name
                for event_payload in qs.using(settings.DATABASE_CONNECTION_REPLICA_NAME)
                if event_payload.payload_file
            ]
            with allow_writer():
                qs.delete()
            delete_files_from_private_storage_task.delay(files_to_delete)
            delete_event_payloads_task.delay(expiration_date)
        else:
            task_logger.error("Task invocation time limit reached, aborting task")


@app.task
def delete_files_from_storage_task(paths):
    for path in paths:
        default_storage.delete(path)


@app.task
def delete_files_from_private_storage_task(paths):
    for path in paths:
        private_storage.delete(path)
