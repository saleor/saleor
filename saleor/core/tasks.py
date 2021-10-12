import datetime

from django.core.files.storage import default_storage

from ..celeryconf import app
from ..settings import EVENT_PAYLOAD_DELETE_PERIOD
from .models import EventDelivery, EventDeliveryAttempt, EventPayload


@app.task
def delete_from_storage_task(path):
    default_storage.delete(path)


@app.task
def delete_event_payloads_task():
    event_payload_delete_period = (
        datetime.datetime.today() - EVENT_PAYLOAD_DELETE_PERIOD
    )
    EventDeliveryAttempt.objects.filter(
        created_at__lte=event_payload_delete_period
    ).delete()
    EventDelivery.objects.filter(created_at__lte=event_payload_delete_period).delete()

    EventPayload.objects.filter(event_tasks__isnull=True).delete()
