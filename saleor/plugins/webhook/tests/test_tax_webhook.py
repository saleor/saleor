from unittest import mock

from freezegun import freeze_time

from ....core import EventDeliveryStatus
from ....core.models import EventDelivery, EventPayload
from ....webhook.event_types import WebhookEventSyncType
from ....webhook.payloads import generate_checkout_payload, generate_order_payload
from ..utils import parse_tax_data


@freeze_time()
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
    payload = EventPayload.objects.get()
    assert payload.payload == generate_checkout_payload(checkout)
    delivery = EventDelivery.objects.get()
    assert delivery.status == EventDeliveryStatus.PENDING
    assert delivery.event_type == WebhookEventSyncType.CHECKOUT_CALCULATE_TAXES
    assert delivery.payload == payload
    assert delivery.webhook == tax_checkout_webhook
    mock_request.assert_called_once_with(tax_checkout_webhook.app.name, delivery)
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


@freeze_time()
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
    payload = EventPayload.objects.get()
    assert payload.payload == generate_order_payload(order)
    delivery = EventDelivery.objects.get()
    assert delivery.status == EventDeliveryStatus.PENDING
    assert delivery.event_type == WebhookEventSyncType.ORDER_CALCULATE_TAXES
    assert delivery.payload == payload
    assert delivery.webhook == tax_order_webhook
    mock_request.assert_called_once_with(tax_order_webhook.app.name, delivery)
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
