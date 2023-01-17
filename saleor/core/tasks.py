from botocore.exceptions import ClientError
from django.conf import settings
from django.core.files.storage import default_storage
from django.db.models import Exists, OuterRef, Q
from django.utils import timezone

from ..celeryconf import app
from .models import EventDelivery, EventDeliveryAttempt, EventPayload


@app.task
def delete_from_storage_task(path):
    default_storage.delete(path)


@app.task
def delete_event_payloads_task():
    delete_period = timezone.now() - settings.EVENT_PAYLOAD_DELETE_PERIOD
    deliveries = EventDelivery.objects.filter(created_at__lte=delete_period)
    attempts = EventDeliveryAttempt.objects.filter(
        Q(Exists(deliveries.filter(id=OuterRef("delivery_id"))))
        | Q(delivery__isnull=True, created_at__lte=delete_period)
    )
    payloads = EventPayload.objects.filter(
        deliveries__isnull=True, created_at__lte=delete_period
    )

    attempts._raw_delete(attempts.db)  # type: ignore[attr-defined] # raw access # noqa: E501
    deliveries._raw_delete(deliveries.db)  # type: ignore[attr-defined] # raw access # noqa: E501
    payloads._raw_delete(payloads.db)  # type: ignore[attr-defined] # raw access # noqa: E501


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
