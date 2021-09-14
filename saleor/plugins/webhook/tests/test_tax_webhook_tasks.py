from unittest import mock
from unittest.mock import Mock

import pytest

from saleor.plugins.webhook.tasks import trigger_tax_webhook_sync
from saleor.plugins.webhook.utils import parse_tax_data
from saleor.webhook.event_types import WebhookEventType
from saleor.webhook.models import Webhook


@pytest.fixture
def tax_checkout_webhooks(tax_app):
    webhooks = []
    for i in range(8):
        webhook = Webhook.objects.create(
            name="Tax checkout webhook",
            app=tax_app,
            target_url="https://www.example.com/tax-checkout",
        )
        webhook.events.create(event_type=WebhookEventType.CHECKOUT_CALCULATE_TAXES)
        webhooks.append(webhook)

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
    tax_data = trigger_tax_webhook_sync(event_type, data)

    # then
    mock_request.assert_called_once_with(
        tax_checkout_webhook.pk,
        tax_checkout_webhook.target_url,
        tax_checkout_webhook.secret_key,
        event_type,
        data,
    )
    assert tax_data == parse_tax_data(tax_data_response)


@pytest.mark.parametrize("no_of_unsuccessful_webhooks", [0, 4, 7])
def test_trigger_tax_webhook_sync_multiple_webhooks(
    tax_checkout_webhooks,
    tax_data_response,
    no_of_unsuccessful_webhooks,
    monkeypatch,
):
    # given
    def new_send_webhook_request_sync(pk, *args):
        if pk == tax_checkout_webhooks[no_of_unsuccessful_webhooks].pk:
            return tax_data_response
        else:
            return {}

    mock_request = Mock(wraps=new_send_webhook_request_sync)
    monkeypatch.setattr(
        "saleor.plugins.webhook.tasks.send_webhook_request_sync", mock_request
    )
    event_type = WebhookEventType.CHECKOUT_CALCULATE_TAXES
    data = '{"key": "value"}'

    # when
    tax_data = trigger_tax_webhook_sync(event_type, data)

    # then
    assert mock_request.call_count == no_of_unsuccessful_webhooks + 1
    for call, webhook in zip(mock_request.call_args_list, tax_checkout_webhooks):
        assert call == (
            (webhook.pk, webhook.target_url, webhook.secret_key, event_type, data),
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
    tax_data = trigger_tax_webhook_sync(event_type, data)

    # then
    assert mock_request.call_count == len(tax_checkout_webhooks)
    assert tax_data is None
