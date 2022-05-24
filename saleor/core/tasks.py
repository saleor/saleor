from botocore.exceptions import ClientError
from django.core.files.storage import default_storage
from django.db.models import Exists, OuterRef, Q
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
    delete_period = timezone.now() - EVENT_PAYLOAD_DELETE_PERIOD
    deliveries = EventDelivery.objects.filter(created_at__lte=delete_period)
    attempts = EventDeliveryAttempt.objects.filter(
        Q(Exists(deliveries.filter(id=OuterRef("delivery_id"))))
        | Q(delivery__isnull=True, created_at__lte=delete_period)
    )
    payloads = EventPayload.objects.filter(
        deliveries__isnull=True, created_at__lte=delete_period
    )

    attempts._raw_delete(attempts.db)
    deliveries._raw_delete(deliveries.db)
    payloads._raw_delete(payloads.db)


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
