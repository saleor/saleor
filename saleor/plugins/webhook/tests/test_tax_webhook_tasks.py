from unittest import mock

import pytest

from ....webhook.event_types import WebhookEventType
from ....webhook.models import Webhook, WebhookEvent
from ..tasks import trigger_tax_webhook_sync
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
            event_type=WebhookEventType.CHECKOUT_CALCULATE_TAXES,
            webhook=webhook,
        )
        for webhook in webhooks
    )

    return webhooks


@mock.patch("saleor.plugins.webhook.tasks.send_webhook_request_sync")
def test_trigger_tax_webhook_sync(
    mock_request,
    tax_checkout_webhook,
    tax_data_response,
):
    # given
    mock_request.return_value = tax_data_response
    event_type = WebhookEventType.CHECKOUT_CALCULATE_TAXES
    data = '{"key": "value"}'

    # when
    tax_data = trigger_tax_webhook_sync(event_type, data, parse_tax_data)

    # then
    mock_request.assert_called_once_with(
        tax_checkout_webhook.app.name,
        tax_checkout_webhook.pk,
        tax_checkout_webhook.target_url,
        tax_checkout_webhook.secret_key,
        event_type,
        data,
    )
    assert tax_data == parse_tax_data(tax_data_response)


@mock.patch("saleor.plugins.webhook.tasks.send_webhook_request_sync")
def test_trigger_tax_webhook_sync_multiple_webhooks_first(
    mock_request,
    tax_checkout_webhooks,
    tax_data_response,
):
    # given
    mock_request.side_effect = [tax_data_response, {}, {}]
    event_type = WebhookEventType.CHECKOUT_CALCULATE_TAXES
    data = '{"key": "value"}'

    # when
    tax_data = trigger_tax_webhook_sync(event_type, data, parse_tax_data)

    # then
    successful_webhook = tax_checkout_webhooks[0]
    mock_request.assert_called_once_with(
        successful_webhook.app.name,
        successful_webhook.pk,
        successful_webhook.target_url,
        successful_webhook.secret_key,
        event_type,
        data,
    )
    assert tax_data == parse_tax_data(tax_data_response)


@mock.patch("saleor.plugins.webhook.tasks.send_webhook_request_sync")
def test_trigger_tax_webhook_sync_multiple_webhooks_last(
    mock_request,
    tax_checkout_webhooks,
    tax_data_response,
):
    # given
    mock_request.side_effect = [{}, {}, tax_data_response]
    event_type = WebhookEventType.CHECKOUT_CALCULATE_TAXES
    data = '{"key": "value"}'

    # when
    tax_data = trigger_tax_webhook_sync(event_type, data, parse_tax_data)

    # then
    assert mock_request.call_count == 3
    for call, webhook in zip(mock_request.call_args_list, tax_checkout_webhooks):
        assert call == (
            (
                webhook.app.name,
                webhook.pk,
                webhook.target_url,
                webhook.secret_key,
                event_type,
                data,
            ),
            {},
        )
    assert tax_data == parse_tax_data(tax_data_response)


@mock.patch("saleor.plugins.webhook.tasks.send_webhook_request_sync")
def test_trigger_tax_webhook_sync_invalid_webhooks(
    mock_request,
    tax_checkout_webhooks,
    tax_data_response,
):
    # given
    mock_request.return_value = {}
    event_type = WebhookEventType.CHECKOUT_CALCULATE_TAXES
    data = '{"key": "value"}'

    # when
    tax_data = trigger_tax_webhook_sync(event_type, data, parse_tax_data)

    # then
    assert mock_request.call_count == len(tax_checkout_webhooks)
    assert tax_data is None
