from unittest import mock
from unittest.mock import Mock

from saleor.plugins.webhook.utils import parse_tax_data
from saleor.webhook.event_types import WebhookEventType
from saleor.webhook.payloads import generate_checkout_payload, generate_order_payload


def test_get_taxes_for_checkout(
    permission_handle_taxes,
    webhook_plugin,
    tax_checkout_webhook,
    tax_data_response,
    checkout,
    tax_app,
    monkeypatch,
):
    # given
    mock_request = Mock(return_value=tax_data_response)
    monkeypatch.setattr(
        "saleor.plugins.webhook.tasks.send_webhook_request_sync", mock_request
    )
    plugin = webhook_plugin()

    # when
    tax_data = plugin.get_taxes_for_checkout(checkout, None)

    # then
    mock_request.assert_called_once_with(
        tax_checkout_webhook.pk,
        tax_checkout_webhook.target_url,
        tax_checkout_webhook.secret_key,
        WebhookEventType.CHECKOUT_CALCULATE_TAXES,
        generate_checkout_payload(checkout),
    )
    assert tax_data == parse_tax_data(tax_data_response)


@mock.patch("saleor.plugins.webhook.tasks.send_webhook_request_sync")
def test_get_taxes_for_checkout_no_permission(
    mock_request,
    webhook_plugin,
    checkout,
    monkeypatch,
):
    # given
    plugin = webhook_plugin()

    # when
    tax_data = plugin.get_taxes_for_checkout(checkout, None)

    # then
    assert mock_request.call_count == 0
    assert tax_data is None


def test_get_taxes_for_order(
    permission_handle_taxes,
    webhook_plugin,
    tax_order_webhook,
    tax_data_response,
    order,
    tax_app,
    monkeypatch,
):
    # given
    mock_request = Mock(return_value=tax_data_response)
    monkeypatch.setattr(
        "saleor.plugins.webhook.tasks.send_webhook_request_sync", mock_request
    )
    plugin = webhook_plugin()

    # when
    tax_data = plugin.get_taxes_for_order(order, None)

    # then
    mock_request.assert_called_once_with(
        tax_order_webhook.pk,
        tax_order_webhook.target_url,
        tax_order_webhook.secret_key,
        WebhookEventType.ORDER_CALCULATE_TAXES,
        generate_order_payload(order),
    )
    assert tax_data == parse_tax_data(tax_data_response)


@mock.patch("saleor.plugins.webhook.tasks.send_webhook_request_sync")
def test_get_taxes_for_order_no_permission(
    mock_request,
    webhook_plugin,
    order,
    monkeypatch,
):
    # given
    plugin = webhook_plugin()

    # when
    tax_data = plugin.get_taxes_for_order(order, None)

    # then
    assert mock_request.call_count == 0
    assert tax_data is None
