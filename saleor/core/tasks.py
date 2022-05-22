from botocore.exceptions import ClientError
from django.core.files.storage import default_storage
from django.utils import timezone

from ..celeryconf import app
from ..product.models import ProductMedia
from ..settings import EVENT_PAYLOAD_DELETE_PERIOD
from .models import EventDelivery, EventDeliveryAttempt, EventPayload
from .utils import delete_versatile_image


@app.task
def delete_from_storage_task(path):
    default_storage.delete(path)


@app.task
def delete_event_payloads_task():
    event_payload_delete_period = timezone.now() - EVENT_PAYLOAD_DELETE_PERIOD
    time_filter = {"created_at__lte": event_payload_delete_period}
    attempts_queryset = EventDeliveryAttempt.objects.filter(**time_filter)
    deliveries_queryset = EventDelivery.objects.filter(**time_filter)
    payloads_queryset = EventPayload.objects.filter(
        deliveries__isnull=True, **time_filter
    )
    attempts_queryset._raw_delete(attempts_queryset.db)
    deliveries_queryset._raw_delete(deliveries_queryset.db)
    payloads_queryset._raw_delete(payloads_queryset.db)


@app.task(
    autoretry_for=(ClientError,),
    retry_backoff=10,
    retry_kwargs={"max_retries": 5},
)
def delete_product_media_task(media_id):
    product_media = ProductMedia.objects.filter(pk=media_id, to_remove=True).first()
    if product_media:
        image_file = product_media.image
        delete_versatile_image(image_file)
        product_media.delete()
