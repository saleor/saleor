from unittest.mock import patch

from .....core.models import EventDelivery, EventDeliveryStatus
from ..transport import trigger_send_webhooks_async_for_apps


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
