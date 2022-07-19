from datetime import timedelta

from django.core.files.storage import default_storage
from django.utils import timezone
from freezegun import freeze_time

from ...webhook.event_types import WebhookEventAsyncType
from ..models import EventDelivery, EventDeliveryAttempt, EventPayload
from ..tasks import delete_event_payloads_task, delete_from_storage_task


def test_delete_from_storage_task(product_with_image, media_root):
    # given
    path = product_with_image.media.first().image.name
    assert default_storage.exists(path)

    # when
    delete_from_storage_task(path)

    # then
    assert not default_storage.exists(path)


def test_delete_from_storage_task_file_that_not_exists(media_root):
    """Ensure method not fail when trying to remove not existing file."""
    # given
    path = "random/test-path"
    assert not default_storage.exists(path)

    # when
    delete_from_storage_task(path)


def test_delete_event_payloads_task(webhook, settings):
    delete_period = settings.EVENT_PAYLOAD_DELETE_PERIOD
    start_time = timezone.now()
    before_delete_period = start_time - delete_period - timedelta(seconds=1)
    after_delete_period = start_time - delete_period + timedelta(seconds=1)
    for creation_time in [before_delete_period, after_delete_period]:
        with freeze_time(creation_time):
            payload = EventPayload.objects.create(payload='{"key": "data"}')
            delivery = EventDelivery.objects.create(
                event_type=WebhookEventAsyncType.ANY,
                payload=payload,
                webhook=webhook,
            )
        with freeze_time(creation_time + timedelta(seconds=2)):
            EventDeliveryAttempt.objects.create(delivery=delivery)

    with freeze_time(start_time):
        delete_event_payloads_task()

    assert EventPayload.objects.count() == 1
    assert EventDelivery.objects.count() == 1
    assert EventDeliveryAttempt.objects.count() == 1
