import json
from unittest import mock
from unittest.mock import sentinel

import pytest
from freezegun import freeze_time

from ....checkout.fetch import fetch_checkout_info, fetch_checkout_lines
from ....core import EventDeliveryStatus
from ....core.models import EventDelivery, EventPayload
from ....core.taxes import TaxType
from ....webhook.event_types import WebhookEventSyncType
from ....webhook.models import Webhook
from ....webhook.payloads import generate_order_payload_for_tax_calculation
from ....webhook.transport.utils import (
    DEFAULT_TAX_CODE,
    DEFAULT_TAX_DESCRIPTION,
    parse_tax_data,
)
from ...manager import get_plugins_manager


@mock.patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
def test_get_taxes_for_checkout_no_permission(
    mock_request,
    webhook_plugin,
    checkout,
):
    # given
    plugin = webhook_plugin()
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, plugin)
    app_identifier = None

    # when
    tax_data = plugin.get_taxes_for_checkout(checkout_info, lines, app_identifier, None)

    # then
    assert mock_request.call_count == 0
    assert tax_data is None


@freeze_time()
@mock.patch("saleor.order.calculations.fetch_order_prices_if_expired")
@mock.patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
def test_get_taxes_for_order(
    mock_request,
    mock_fetch,
    permission_handle_taxes,
    webhook_plugin,
    tax_order_webhook,
    tax_data_response,
    order,
    tax_app_with_webhooks,
):
    # given
    mock_request.return_value = tax_data_response
    plugin = webhook_plugin()
    app_identifier = None

    # when
    tax_data = plugin.get_taxes_for_order(order, app_identifier, None)

    # then
    payload = EventPayload.objects.get()
    assert payload.payload == generate_order_payload_for_tax_calculation(order)
    delivery = EventDelivery.objects.get()
    assert delivery.status == EventDeliveryStatus.PENDING
    assert delivery.event_type == WebhookEventSyncType.ORDER_CALCULATE_TAXES
    assert delivery.payload == payload
    assert delivery.webhook == tax_order_webhook
    mock_request.assert_called_once_with(delivery)
    mock_fetch.assert_not_called()
    assert tax_data == parse_tax_data(tax_data_response)


@mock.patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
def test_get_taxes_for_order_no_permission(
    mock_request,
    webhook_plugin,
    order,
):
    # given
    plugin = webhook_plugin()
    app_identifier = None

    # when
    tax_data = plugin.get_taxes_for_order(order, app_identifier, None)

    # then
    assert mock_request.call_count == 0
    assert tax_data is None


@pytest.fixture
def tax_type():
    return TaxType(
        code="code_2",
        description="description_2",
    )


def test_get_tax_code_from_object_meta_no_app(
    webhook_plugin,
    product,
):
    # given
    plugin = webhook_plugin()
    previous_value = sentinel.PREVIOUS_VALUE

    # when
    fetched_tax_type = plugin.get_tax_code_from_object_meta(product, previous_value)

    # then
    assert fetched_tax_type == previous_value


def test_get_tax_code_from_object_meta(
    webhook_plugin,
    tax_app_with_webhooks,
    tax_type,
    product,
):
    # given
    plugin = webhook_plugin()
    product.metadata = {
        f"{tax_app_with_webhooks.identifier}.code": tax_type.code,
        f"{tax_app_with_webhooks.identifier}.description": tax_type.description,
    }

    # when
    fetched_tax_type = plugin.get_tax_code_from_object_meta(product, None)

    # then
    assert fetched_tax_type == tax_type


def test_get_tax_code_from_object_meta_default_code(
    webhook_plugin,
    tax_app_with_webhooks,
    product,
):
    # given
    plugin = webhook_plugin()

    # when
    fetched_tax_type = plugin.get_tax_code_from_object_meta(product, None)

    # then
    assert fetched_tax_type == TaxType(
        code=DEFAULT_TAX_CODE,
        description=DEFAULT_TAX_DESCRIPTION,
    )


@freeze_time()
@mock.patch("saleor.order.calculations.fetch_order_prices_if_expired")
@mock.patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
def test_get_taxes_for_order_with_sync_subscription(
    mock_request,
    mock_fetch,
    webhook_plugin,
    tax_data_response,
    order,
    tax_app,
):
    # given
    mock_request.return_value = tax_data_response
    plugin = webhook_plugin()
    webhook = Webhook.objects.create(
        name="Tax checkout webhook",
        app=tax_app,
        target_url="https://localhost:8888/tax-order",
        subscription_query=(
            "subscription{event{... on CalculateTaxes{taxBase{currency}}}}"
        ),
    )
    webhook.events.create(event_type=WebhookEventSyncType.ORDER_CALCULATE_TAXES)
    app_identifier = None

    # when
    tax_data = plugin.get_taxes_for_order(order, app_identifier, None)

    # then
    payload = EventPayload.objects.get()
    assert payload.payload == json.dumps({"taxBase": {"currency": "USD"}})
    delivery = EventDelivery.objects.get()
    assert delivery.status == EventDeliveryStatus.PENDING
    assert delivery.event_type == WebhookEventSyncType.ORDER_CALCULATE_TAXES
    assert delivery.payload == payload
    assert delivery.webhook == webhook
    mock_request.assert_called_once_with(delivery)
    mock_fetch.assert_not_called()
    assert tax_data == parse_tax_data(tax_data_response)


@freeze_time()
@mock.patch("saleor.checkout.calculations.fetch_checkout_data")
@mock.patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
def test_get_taxes_for_checkout_with_sync_subscription(
    mock_request,
    mock_fetch,
    webhook_plugin,
    tax_data_response,
    checkout,
    tax_app,
):
    # given
    checkout_info = fetch_checkout_info(
        checkout, [], get_plugins_manager(allow_replica=False)
    )
    mock_request.return_value = tax_data_response
    plugin = webhook_plugin()
    webhook = Webhook.objects.create(
        name="Tax checkout webhook",
        app=tax_app,
        target_url="https://localhost:8888/tax-order",
        subscription_query=(
            "subscription{event{... on CalculateTaxes{taxBase{currency}}}}"
        ),
    )
    webhook.events.create(event_type=WebhookEventSyncType.CHECKOUT_CALCULATE_TAXES)
    app_identifier = None

    # when
    tax_data = plugin.get_taxes_for_checkout(checkout_info, [], app_identifier, None)

    # then
    payload = EventPayload.objects.get()
    assert payload.payload == json.dumps({"taxBase": {"currency": "USD"}})
    delivery = EventDelivery.objects.get()
    assert delivery.status == EventDeliveryStatus.PENDING
    assert delivery.event_type == WebhookEventSyncType.CHECKOUT_CALCULATE_TAXES
    assert delivery.payload == payload
    assert delivery.webhook == webhook
    mock_request.assert_called_once_with(delivery)
    mock_fetch.assert_not_called()
    assert tax_data == parse_tax_data(tax_data_response)


@mock.patch("saleor.webhook.transport.synchronous.transport.trigger_all_webhooks_sync")
def test_get_taxes_for_order_log_address_if_validation_skipped(
    mock_webhook_trigger,
    webhook_plugin,
    address,
    order,
    tax_app,
    caplog,
):
    # given
    plugin = webhook_plugin()
    app_identifier = None

    address.validation_skipped = True
    address.postal_code = "invalid postal code"
    address.save(update_fields=["postal_code", "validation_skipped"])
    order.shipping_address = address
    order.billing_address = address
    order.save(update_fields=["shipping_address", "billing_address"])

    # when
    plugin.get_taxes_for_order(order, app_identifier, None)

    # then
    assert (
        f"Fetching tax data for order with address validation skipped. "
        f"Address ID: {address.pk}" in caplog.text
    )


@mock.patch("saleor.webhook.transport.synchronous.transport.trigger_all_webhooks_sync")
def test_get_taxes_for_checkout_log_address_if_validation_skipped(
    mock_webhook_trigger,
    webhook_plugin,
    address,
    checkout_info,
    tax_app,
    caplog,
):
    # given
    plugin = webhook_plugin()
    app_identifier = None

    address.validation_skipped = True
    address.postal_code = "invalid postal code"
    address.save(update_fields=["postal_code", "validation_skipped"])

    checkout_info.shipping_address = address
    checkout_info.billing_address = address

    # when
    plugin.get_taxes_for_checkout(checkout_info, None, app_identifier, None)

    # then
    assert (
        f"Fetching tax data for checkout with address validation skipped. "
        f"Address ID: {address.pk}" in caplog.text
    )
