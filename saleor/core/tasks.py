import datetime

from django.core.files.storage import default_storage

from ..celeryconf import app
from .models import EventPayload, EventTask


@app.task
def delete_from_storage_task(path):
    default_storage.delete(path)


@app.task
def delete_event_payloads():
    seven_days_ago = datetime.date.today() - datetime.timedelta(days=7)

    EventTask.objects.filter(created_at__lte=seven_days_ago).detele()

    EventPayload.objects.filter(event_payloads__isnull=True).delete()
