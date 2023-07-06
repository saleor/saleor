from botocore.exceptions import ClientError
from django.conf import settings
from django.core.files.storage import default_storage
from django.db.models import Exists, OuterRef
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
    valid_deliveries = EventDelivery.objects.filter(created_at__gt=delete_period)
    payloads_to_delete = EventPayload.objects.filter(
        ~Exists(valid_deliveries.filter(payload_id=OuterRef("id")))
    ).order_by('-pk')
    ids = payloads_to_delete.values_list("pk", flat=True)[:BATCH_SIZE]
    qs = EventPayload.objects.filter(pk__in=ids)
    if ids:
        qs.delete()
        delete_event_payloads_task.delay()


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
