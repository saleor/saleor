from unittest import mock

from ....webhook.event_types import WebhookEventType
from ....webhook.payloads import generate_checkout_payload, generate_order_payload
from ..utils import parse_tax_data


@mock.patch("saleor.plugins.webhook.tasks.send_webhook_request_sync")
def test_get_taxes_for_checkout(
    mock_request,
    permission_handle_taxes,
    webhook_plugin,
    tax_checkout_webhook,
    tax_data_response,
    checkout,
    tax_app,
):
    # given
    mock_request.return_value = tax_data_response
    plugin = webhook_plugin()

    # when
    tax_data = plugin.get_taxes_for_checkout(checkout, None)

    # then
    mock_request.assert_called_once_with(
        tax_checkout_webhook.app.name,
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
):
    # given
    plugin = webhook_plugin()

    # when
    tax_data = plugin.get_taxes_for_checkout(checkout, None)

    # then
    assert mock_request.call_count == 0
    assert tax_data is None


@mock.patch("saleor.plugins.webhook.tasks.send_webhook_request_sync")
def test_get_taxes_for_order(
    mock_request,
    permission_handle_taxes,
    webhook_plugin,
    tax_order_webhook,
    tax_data_response,
    order,
    tax_app,
):
    # given
    mock_request.return_value = tax_data_response
    plugin = webhook_plugin()

    # when
    tax_data = plugin.get_taxes_for_order(order, None)

    # then
    mock_request.assert_called_once_with(
        tax_order_webhook.app.name,
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
):
    # given
    plugin = webhook_plugin()

    # when
    tax_data = plugin.get_taxes_for_order(order, None)

    # then
    assert mock_request.call_count == 0
    assert tax_data is None
