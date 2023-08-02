from unittest import mock

import pytest

from ....core import EventDeliveryStatus
from ....core.models import EventDelivery, EventPayload
from ....webhook.event_types import WebhookEventSyncType
from ....webhook.models import Webhook, WebhookEvent
from ..tasks import trigger_all_webhooks_sync
from ..utils import parse_tax_data


@pytest.fixture
def tax_checkout_webhooks(tax_app):
    webhooks = [
        Webhook(
            name=f"Tax checkout webhook no {i}",
            app=tax_app,
            target_url=f"https://www.example.com/tax-checkout-{i}",
        )
        for i in range(3)
    ]
    Webhook.objects.bulk_create(webhooks)
    WebhookEvent.objects.bulk_create(
        WebhookEvent(
            event_type=WebhookEventSyncType.CHECKOUT_CALCULATE_TAXES,
            webhook=webhook,
        )
        for webhook in webhooks
    )

    return list(
        Webhook.objects.filter(
            events__event_type=WebhookEventSyncType.CHECKOUT_CALCULATE_TAXES
        )
    )


@mock.patch("saleor.plugins.webhook.tasks.send_webhook_request_sync")
def test_trigger_tax_webhook_sync(
    mock_request,
    tax_checkout_webhook,
    tax_data_response,
):
    # given
    mock_request.return_value = tax_data_response
    event_type = WebhookEventSyncType.CHECKOUT_CALCULATE_TAXES
    data = '{"key": "value"}'

    # when
    tax_data = trigger_all_webhooks_sync(event_type, lambda: data, parse_tax_data)

    # then
    payload = EventPayload.objects.get()
    assert payload.payload == data
    delivery = EventDelivery.objects.get()
    assert delivery.status == EventDeliveryStatus.PENDING
    assert delivery.event_type == event_type
    assert delivery.payload == payload
    assert delivery.webhook == tax_checkout_webhook
    mock_request.assert_called_once_with(delivery)
    assert tax_data == parse_tax_data(tax_data_response)


@mock.patch("saleor.plugins.webhook.tasks.send_webhook_request_sync")
def test_trigger_tax_webhook_sync_multiple_webhooks_first(
    mock_request,
    tax_checkout_webhooks,
    tax_data_response,
):
    # given
    mock_request.side_effect = [tax_data_response, {}, {}]
    event_type = WebhookEventSyncType.CHECKOUT_CALCULATE_TAXES
    data = '{"key": "value"}'

    # when
    tax_data = trigger_all_webhooks_sync(event_type, lambda: data, parse_tax_data)

    # then
    successful_webhook = tax_checkout_webhooks[0]

    payload = EventPayload.objects.get()
    assert payload.payload == data
    delivery = EventDelivery.objects.order_by("pk").first()
    assert delivery.status == EventDeliveryStatus.PENDING
    assert delivery.event_type == event_type
    assert delivery.payload == payload
    assert delivery.webhook == successful_webhook
    mock_request.assert_called_once_with(delivery)
    assert tax_data == parse_tax_data(tax_data_response)


@mock.patch("saleor.plugins.webhook.tasks.send_webhook_request_sync")
def test_trigger_tax_webhook_sync_multiple_webhooks_last(
    mock_request,
    tax_checkout_webhooks,
    tax_data_response,
):
    # given
    mock_request.side_effect = [{}, {}, tax_data_response]
    event_type = WebhookEventSyncType.CHECKOUT_CALCULATE_TAXES
    data = '{"key": "value"}'

    # when
    tax_data = trigger_all_webhooks_sync(event_type, lambda: data, parse_tax_data)

    # then

    payload = EventPayload.objects.get()
    assert payload.payload == data
    deliveries = list(EventDelivery.objects.order_by("pk"))
    for call, delivery, webhook in zip(
        mock_request.call_args_list, deliveries, tax_checkout_webhooks
    ):
        assert delivery.status == EventDeliveryStatus.PENDING
        assert delivery.event_type == event_type
        assert delivery.payload == payload
        assert delivery.webhook == webhook
        assert call[0] == (delivery,)

    assert mock_request.call_count == 3
    assert tax_data == parse_tax_data(tax_data_response)


@mock.patch("saleor.plugins.webhook.tasks.send_webhook_request_sync")
def test_trigger_tax_webhook_sync_invalid_webhooks(
    mock_request,
    tax_checkout_webhooks,
    tax_data_response,
):
    # given
    mock_request.return_value = {}
    event_type = WebhookEventSyncType.CHECKOUT_CALCULATE_TAXES
    data = '{"key": "value"}'

    # when
    tax_data = trigger_all_webhooks_sync(event_type, lambda: data, parse_tax_data)

    # then
    assert mock_request.call_count == len(tax_checkout_webhooks)
    assert tax_data is None
