from unittest import mock

import pytest

from ...core import EventDeliveryStatus
from ...core.models import EventDelivery
from ..event_types import WebhookEventSyncType
from ..models import Webhook, WebhookEvent
from ..transport.synchronous import trigger_all_webhooks_sync
from ..transport.utils import parse_tax_data


@pytest.fixture
def tax_checkout_webhooks(tax_app):
    tax_app.webhooks.all().delete()
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


@mock.patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
def test_trigger_tax_webhook_sync(
    mock_request,
    tax_app,
    tax_data_response,
):
    # given
    mock_request.return_value = tax_data_response
    event_type = WebhookEventSyncType.CHECKOUT_CALCULATE_TAXES
    data = '{"key": "value"}'
    webhook = tax_app.webhooks.get(name="tax-webhook-1")
    webhook.subscription_query = None
    webhook.save(update_fields=["subscription_query"])

    # when
    tax_data = trigger_all_webhooks_sync(event_type, lambda: data, parse_tax_data)

    # then
    mock_request.assert_called_once()
    assert not EventDelivery.objects.exists()
    delivery = mock_request.mock_calls[0].args[0]

    assert delivery.payload.get_payload() == data
    assert delivery.status == EventDeliveryStatus.PENDING
    assert delivery.event_type == event_type
    assert delivery.webhook == webhook
    assert tax_data == parse_tax_data(tax_data_response)


@mock.patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
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
    mock_request.assert_called_once()
    assert not EventDelivery.objects.exists()
    delivery = mock_request.mock_calls[0].args[0]
    assert delivery.payload.get_payload() == data
    assert delivery.status == EventDeliveryStatus.PENDING
    assert delivery.event_type == event_type
    assert delivery.webhook == successful_webhook
    assert tax_data == parse_tax_data(tax_data_response)


@mock.patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
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
    assert mock_request.call_count == 3
    assert not EventDelivery.objects.exists()

    for call, webhook in zip(mock_request.mock_calls, tax_checkout_webhooks):
        delivery = call.args[0]
        assert delivery.status == EventDeliveryStatus.PENDING
        assert delivery.event_type == event_type
        assert delivery.payload.get_payload() == data
        assert delivery.webhook == webhook

    assert tax_data == parse_tax_data(tax_data_response)


@mock.patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
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
