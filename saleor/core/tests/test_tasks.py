from datetime import timedelta
from unittest.mock import MagicMock, patch

import pytest
from django.core.files import File
from django.core.files.storage import default_storage
from django.utils import timezone
from freezegun import freeze_time

from ...product.models import ProductMedia
from ...thumbnail.models import Thumbnail
from ...webhook.event_types import WebhookEventAsyncType
from ..models import EventDelivery, EventDeliveryAttempt, EventPayload
from ..tasks import (
    delete_event_payloads_task,
    delete_from_storage_task,
    delete_product_media_task,
)


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


@patch("saleor.thumbnail.signals.delete_from_storage_task.delay")
def test_delete_product_media_task_product_media_not_to_remove(
    delete_from_storage_task_mock, product_with_image
):
    # given
    media = product_with_image.media.first()

    thumbnail_mock = MagicMock(spec=File)
    thumbnail_mock.name = "thumbnail_image.jpg"
    thumbnail = Thumbnail.objects.create(
        product_media=media, size=128, image=thumbnail_mock
    )

    # when
    delete_product_media_task(media.pk)

    # then
    delete_from_storage_task_mock.assert_not_called()
    media.refresh_from_db()
    ProductMedia.objects.filter(product=product_with_image).exists()
    thumbnail.refresh_from_db()
    Thumbnail.objects.filter(product_media=media).exists()


@patch("saleor.thumbnail.signals.delete_from_storage_task.delay")
def test_delete_product_media_task_product_media_to_remove(
    delete_from_storage_task_mock, product_with_image
):
    # given
    media = product_with_image.media.first()
    media.to_remove = True
    media.save(update_fields=["to_remove"])

    thumbnail_mock = MagicMock(spec=File)
    thumbnail_mock.name = "thumbnail_image.jpg"
    thumbnail = Thumbnail.objects.create(
        product_media=media, size=128, image=thumbnail_mock
    )

    # when
    delete_product_media_task(media.pk)

    # then
    with pytest.raises(media._meta.model.DoesNotExist):
        media.refresh_from_db()
    with pytest.raises(thumbnail._meta.model.DoesNotExist):
        thumbnail.refresh_from_db()

    delete_from_storage_task_mock.assert_called_once_with(thumbnail.image.name)


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
