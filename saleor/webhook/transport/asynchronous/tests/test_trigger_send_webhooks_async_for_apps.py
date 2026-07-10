import threading
from unittest.mock import patch

import pytest
from django.db import transaction

from .....app.models import App, AppWebhookMutex
from .....core.models import EventDelivery, EventDeliveryStatus
from .....webhook.event_types import WebhookEventAsyncType
from .....webhook.models import Webhook
from ..transport import trigger_send_webhooks_async_for_apps


@pytest.fixture
def second_app_event_delivery(event_payload):
    """Return a pending event delivery belonging to a separate app."""
    second_app = App.objects.create(
        name="Second app",
        is_active=True,
        identifier="saleor.app.second",
    )
    webhook = Webhook.objects.create(
        name="Second app webhook",
        app=second_app,
        target_url="http://www.example.com/second",
    )
    return EventDelivery.objects.create(
        event_type=WebhookEventAsyncType.ANY,
        payload=event_payload,
        webhook=webhook,
    )


@patch(
    "saleor.webhook.transport.asynchronous.transport.send_webhooks_async_for_app.apply_async"
)
def test_trigger_send_webhooks_async_for_apps(
    mock_apply_async,
    event_delivery,
    app,
):
    # given
    assert EventDelivery.objects.filter(status=EventDeliveryStatus.PENDING).exists()

    # when
    trigger_send_webhooks_async_for_apps()

    # then
    mock_apply_async.assert_called_once()
    call_kwargs = mock_apply_async.call_args
    assert call_kwargs.kwargs["kwargs"]["app_id"] == app.id


@patch(
    "saleor.webhook.transport.asynchronous.transport.send_webhooks_async_for_app.apply_async"
)
def test_trigger_send_webhooks_async_for_apps_no_deliveries(
    mock_apply_async,
):
    # given
    assert not EventDelivery.objects.filter(status=EventDeliveryStatus.PENDING).exists()

    # when
    trigger_send_webhooks_async_for_apps()

    # then
    mock_apply_async.assert_not_called()


@patch(
    "saleor.webhook.transport.asynchronous.transport.send_webhooks_async_for_app.apply_async"
)
def test_trigger_send_webhooks_async_for_apps_skips_non_pending(
    mock_apply_async,
    event_delivery,
):
    # given
    event_delivery.status = EventDeliveryStatus.FAILED
    event_delivery.save()

    # when
    trigger_send_webhooks_async_for_apps()

    # then
    mock_apply_async.assert_not_called()


@patch(
    "saleor.webhook.transport.asynchronous.transport.send_webhooks_async_for_app.apply_async"
)
def test_trigger_send_webhooks_async_for_apps_skips_deliveries_without_payload(
    mock_apply_async,
    event_delivery,
):
    # given
    event_delivery.payload = None
    event_delivery.save()

    # when
    trigger_send_webhooks_async_for_apps()

    # then
    mock_apply_async.assert_not_called()


@patch(
    "saleor.webhook.transport.asynchronous.transport.send_webhooks_async_for_app.apply_async"
)
def test_trigger_send_webhooks_async_for_apps_distinct_apps(
    mock_apply_async,
    event_deliveries,
):
    # given
    # event_deliveries fixture creates 3 deliveries for the same app
    assert EventDelivery.objects.filter(status=EventDeliveryStatus.PENDING).count() > 1

    # when
    trigger_send_webhooks_async_for_apps()

    # then
    # only one call since all deliveries belong to the same app
    mock_apply_async.assert_called_once()


@patch(
    "saleor.webhook.transport.asynchronous.transport.send_webhooks_async_for_app.apply_async"
)
def test_trigger_send_webhooks_async_for_apps_mutex_row_exists_and_not_locked(
    mock_apply_async,
    event_delivery,
    app,
):
    # given
    AppWebhookMutex.objects.create(app=app)

    # when
    trigger_send_webhooks_async_for_apps()

    # then
    mock_apply_async.assert_called_once()
    assert mock_apply_async.call_args.kwargs["kwargs"]["app_id"] == app.id


@pytest.mark.django_db(transaction=True)
@patch(
    "saleor.webhook.transport.asynchronous.transport.send_webhooks_async_for_app.apply_async"
)
def test_trigger_send_webhooks_async_for_apps_skips_app_with_webhook_lock_taken(
    mock_apply_async,
    event_delivery,
    app,
    second_app_event_delivery,
    django_db_blocker,
):
    """Hold the app's webhook lock in a second thread while the trigger runs.

    The busy app must not be scheduled, while the app with a free lock must be.
    """
    # given
    AppWebhookMutex.objects.create(app=app)
    second_app = second_app_event_delivery.webhook.app

    lock_held = threading.Event()
    release_lock = threading.Event()

    def hold_lock():
        with django_db_blocker.unblock():
            with transaction.atomic():
                AppWebhookMutex.objects.select_for_update(
                    nowait=True, of=("self",)
                ).get(app_id=app.id)
                lock_held.set()
                # keep the row locked until the main thread has run the trigger
                release_lock.wait(timeout=5)

    holder = threading.Thread(target=hold_lock)
    holder.start()
    assert lock_held.wait(timeout=5), "background thread failed to acquire the lock"

    try:
        # when
        trigger_send_webhooks_async_for_apps()
    finally:
        release_lock.set()
        holder.join(timeout=5)

    # then
    mock_apply_async.assert_called_once()
    assert mock_apply_async.call_args.kwargs["kwargs"]["app_id"] == second_app.id
