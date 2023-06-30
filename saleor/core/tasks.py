from botocore.exceptions import ClientError
from django.conf import settings
from django.core.files.storage import default_storage
from django.utils import timezone

from ..celeryconf import app
from .models import EventDelivery, EventPayload

BATCH_SIZE = 100


@app.task
def delete_from_storage_task(path):
    default_storage.delete(path)


@app.task
def delete_event_payloads_task():
    delete_period = timezone.now() - settings.EVENT_PAYLOAD_DELETE_PERIOD
    deliveries = EventDelivery.objects.filter(
        created_at__lte=delete_period
    ).order_by("-pk")
    ids = deliveries.values_list("pk", flat=True)[:BATCH_SIZE]
    qs = EventDelivery.objects.filter(pk__in=ids)
    if ids:
        qs.delete()
        delete_event_payloads_task.delay()
    else:
        delete_unused_payloads.delay()


@app.task(
    autoretry_for=(ClientError,),
    retry_backoff=10,
    retry_kwargs={"max_retries": 5},
)
def delete_product_media_task(media_id):
    # TODO: to delete
    pass


@app.task
def delete_files_from_storage_task(paths):
    for path in paths:
        default_storage.delete(path)


@app.task
def delete_unused_payloads():
    delete_period = timezone.now() - settings.EVENT_PAYLOAD_DELETE_PERIOD

    payloads = EventPayload.objects.filter(
        deliveries__isnull=True, created_at__lte=delete_period
    ).order_by("-pk")
    ids = payloads.values_list("pk", flat=True)[:BATCH_SIZE]
    qs = EventPayload.objects.filter(pk__in=ids)
    if ids:
        qs.delete()

