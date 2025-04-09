import json
from unittest import mock
from unittest.mock import ANY, sentinel

import pytest
from freezegun import freeze_time

from ....checkout.fetch import fetch_checkout_info, fetch_checkout_lines
from ....core import EventDeliveryStatus
from ....core.models import EventDelivery
from ....core.taxes import TaxDataError, TaxType
from ....graphql.webhook.utils import get_subscription_query_hash
from ....webhook.event_types import WebhookEventSyncType
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
    checkout_info = fetch_checkout_info(
        checkout, lines, get_plugins_manager(allow_replica=False)
    )
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
    tax_data_response,
    order,
    tax_app,
):
    # given
    mock_request.return_value = tax_data_response
    plugin = webhook_plugin()
    app_identifier = None
    webhook = tax_app.webhooks.get(name="tax-webhook-1")
    webhook.subscription_query = None
    webhook.save(update_fields=["subscription_query"])

    # when
    tax_data = plugin.get_taxes_for_order(order, app_identifier, None)

    # then
    mock_request.assert_called_once()
    assert not EventDelivery.objects.exists()

    delivery = mock_request.mock_calls[0].args[0]
    assert delivery.payload.get_payload() == generate_order_payload_for_tax_calculation(
        order
    )
    assert delivery.status == EventDeliveryStatus.PENDING
    assert delivery.event_type == WebhookEventSyncType.ORDER_CALCULATE_TAXES
    assert delivery.webhook == webhook
    mock_fetch.assert_not_called()
    assert tax_data == parse_tax_data(tax_data_response, order.lines.count())


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
    tax_app,
    tax_type,
    product,
):
    # given
    plugin = webhook_plugin()
    product.metadata = {
        f"{tax_app.identifier}.code": tax_type.code,
        f"{tax_app.identifier}.description": tax_type.description,
    }

    # when
    fetched_tax_type = plugin.get_tax_code_from_object_meta(product, None)

    # then
    assert fetched_tax_type == tax_type


def test_get_tax_code_from_object_meta_default_code(
    webhook_plugin,
    tax_app,
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
    webhook = tax_app.webhooks.get(name="tax-webhook-1")
    webhook.subscription_query = (
        "subscription{event{... on CalculateTaxes{taxBase{currency}}}}"
    )
    webhook.save(update_fields=["subscription_query"])
    app_identifier = None

    # when
    tax_data = plugin.get_taxes_for_order(order, app_identifier, None)

    # then
    mock_request.assert_called_once()
    assert not EventDelivery.objects.exists()

    delivery = mock_request.mock_calls[0].args[0]
    assert delivery.payload.get_payload() == json.dumps(
        {"taxBase": {"currency": "USD"}}
    )
    assert delivery.status == EventDeliveryStatus.PENDING
    assert delivery.event_type == WebhookEventSyncType.ORDER_CALCULATE_TAXES
    assert delivery.webhook == webhook
    mock_fetch.assert_not_called()
    assert tax_data == parse_tax_data(tax_data_response, order.lines.count())


@freeze_time()
@mock.patch("saleor.checkout.calculations.fetch_checkout_data")
@mock.patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
@mock.patch(
    "saleor.webhook.transport.synchronous.transport.generate_payload_from_subscription"
)
def test_get_taxes_for_checkout_with_sync_subscription(
    mock_generate_payload,
    mock_request,
    mock_fetch,
    webhook_plugin,
    tax_data_response,
    checkout,
    tax_app,
):
    # given
    subscription_query = "subscription{event{... on CalculateTaxes{taxBase{currency}}}}"
    expected_payload = {"taxBase": {"currency": "USD"}}
    checkout_info = fetch_checkout_info(
        checkout, [], get_plugins_manager(allow_replica=False)
    )
    mock_request.return_value = tax_data_response
    mock_generate_payload.return_value = expected_payload
    plugin = webhook_plugin()
    webhook = tax_app.webhooks.get(name="tax-webhook-1")
    webhook.subscription_query = subscription_query
    webhook.save(update_fields=["subscription_query"])
    app_identifier = None

    # when
    tax_data = plugin.get_taxes_for_checkout(checkout_info, [], app_identifier, None)

    # then
    mock_generate_payload.assert_called_once_with(
        event_type=WebhookEventSyncType.CHECKOUT_CALCULATE_TAXES,
        subscribable_object=checkout,
        subscription_query=subscription_query,
        request=ANY,  # SaleorContext,
        app=tax_app,
    )
    mock_request.assert_called_once()
    assert not EventDelivery.objects.exists()

    delivery = mock_request.mock_calls[0].args[0]
    assert delivery.payload.get_payload() == json.dumps(expected_payload)
    assert delivery.status == EventDeliveryStatus.PENDING
    assert delivery.event_type == WebhookEventSyncType.CHECKOUT_CALCULATE_TAXES
    assert delivery.webhook == webhook
    mock_fetch.assert_not_called()
    assert tax_data == parse_tax_data(tax_data_response, checkout.lines.count())


@freeze_time()
@mock.patch("saleor.checkout.calculations.fetch_checkout_data")
@mock.patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
@mock.patch(
    "saleor.webhook.transport.synchronous.transport.generate_payload_from_subscription"
)
def test_get_taxes_for_checkout_with_sync_subscription_with_pregenerated_payload(
    mock_generate_payload,
    mock_request,
    mock_fetch,
    webhook_plugin,
    tax_data_response,
    checkout,
    tax_app,
):
    # given
    subscription_query = "subscription{event{... on CalculateTaxes{taxBase{currency}}}}"
    subscription_query_hash = get_subscription_query_hash(subscription_query)
    expected_payload = {"taxBase": {"currency": "USD"}}
    checkout_info = fetch_checkout_info(
        checkout, [], get_plugins_manager(allow_replica=False)
    )
    mock_request.return_value = tax_data_response
    plugin = webhook_plugin()
    webhook = tax_app.webhooks.get(name="tax-webhook-1")
    webhook.subscription_query = subscription_query
    webhook.save(update_fields=["subscription_query"])
    app_identifier = None
    pregenerated_subscription_payloads = {
        webhook.app.id: {subscription_query_hash: expected_payload}
    }

    # when
    tax_data = plugin.get_taxes_for_checkout(
        checkout_info,
        [],
        app_identifier,
        None,
        pregenerated_subscription_payloads=pregenerated_subscription_payloads,
    )

    # then
    mock_generate_payload.assert_not_called()
    mock_request.assert_called_once()
    assert not EventDelivery.objects.exists()

    delivery = mock_request.mock_calls[0].args[0]
    assert delivery.payload.get_payload() == json.dumps(expected_payload)
    assert delivery.status == EventDeliveryStatus.PENDING
    assert delivery.event_type == WebhookEventSyncType.CHECKOUT_CALCULATE_TAXES
    assert delivery.webhook == webhook
    mock_fetch.assert_not_called()
    assert tax_data == parse_tax_data(tax_data_response, checkout.lines.count())


def test_get_taxes_for_checkout_with_app_identifier_app_missing(
    checkout_info, webhook_plugin
):
    # given
    app_identifier = "missing_app"
    plugin = webhook_plugin()

    # when & then
    with pytest.raises(TaxDataError, match="Configured tax app doesn't exist."):
        plugin.get_taxes_for_checkout(
            checkout_info, checkout_info.lines, app_identifier, None
        )


def test_get_taxes_for_checkout_with_app_identifier_webhook_is_missing(
    checkout_info, webhook_plugin, app
):
    # given
    plugin = webhook_plugin()

    # when & then
    with pytest.raises(
        TaxDataError,
        match="Configured tax app's webhook for taxes calculation doesn't exists.",
    ):
        plugin.get_taxes_for_checkout(
            checkout_info, checkout_info.lines, app.identifier, None
        )


@mock.patch("saleor.checkout.calculations.fetch_checkout_data")
@mock.patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
@mock.patch(
    "saleor.webhook.transport.synchronous.transport.generate_payload_from_subscription"
)
def test_get_taxes_for_checkout_with_app_identifier_invalid_response(
    mock_generate_payload,
    mock_request,
    mock_fetch,
    webhook_plugin,
    tax_data_response_factory,
    checkout,
    tax_app,
):
    # given
    subscription_query = "subscription{event{... on CalculateTaxes{taxBase{currency}}}}"
    expected_payload = {"taxBase": {"currency": "USD"}}
    checkout_info = fetch_checkout_info(
        checkout, [], get_plugins_manager(allow_replica=False)
    )
    # mock returning invalid data - tax_rate above 100
    mock_request.return_value = tax_data_response_factory(shipping_tax_rate=120)
    mock_generate_payload.return_value = expected_payload
    plugin = webhook_plugin()
    webhook = tax_app.webhooks.get(name="tax-webhook-1")
    webhook.subscription_query = subscription_query
    webhook.save(update_fields=["subscription_query"])
    app_identifier = tax_app.identifier

    # when
    with pytest.raises(TaxDataError):
        plugin.get_taxes_for_checkout(checkout_info, [], app_identifier, None)


@freeze_time()
@mock.patch("saleor.checkout.calculations.fetch_checkout_data")
@mock.patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
@mock.patch(
    "saleor.webhook.transport.synchronous.transport.generate_payload_from_subscription"
)
def test_get_taxes_for_checkout_with_app_identifier(
    mock_generate_payload,
    mock_request,
    mock_fetch,
    webhook_plugin,
    tax_data_response,
    checkout,
    tax_app,
):
    # given
    subscription_query = "subscription{event{... on CalculateTaxes{taxBase{currency}}}}"
    expected_payload = {"taxBase": {"currency": "USD"}}
    checkout_info = fetch_checkout_info(
        checkout, [], get_plugins_manager(allow_replica=False)
    )
    mock_request.return_value = tax_data_response
    mock_generate_payload.return_value = expected_payload
    plugin = webhook_plugin()
    webhook = tax_app.webhooks.get(name="tax-webhook-1")
    webhook.subscription_query = subscription_query
    webhook.save(update_fields=["subscription_query"])
    app_identifier = tax_app.identifier

    # when
    tax_data = plugin.get_taxes_for_checkout(checkout_info, [], app_identifier, None)

    # then
    mock_generate_payload.assert_called_once_with(
        event_type=WebhookEventSyncType.CHECKOUT_CALCULATE_TAXES,
        subscribable_object=checkout,
        subscription_query=subscription_query,
        request=ANY,  # SaleorContext,
        app=tax_app,
    )
    mock_request.assert_called_once()
    assert not EventDelivery.objects.exists()

    delivery = mock_request.mock_calls[0].args[0]
    assert delivery.payload.get_payload() == json.dumps(expected_payload)
    assert delivery.status == EventDeliveryStatus.PENDING
    assert delivery.event_type == WebhookEventSyncType.CHECKOUT_CALCULATE_TAXES
    assert delivery.webhook == webhook
    mock_fetch.assert_not_called()
    assert tax_data == parse_tax_data(tax_data_response, checkout.lines.count())


def test_get_taxes_for_order_with_app_identifier_app_missing(order, webhook_plugin):
    # given
    app_identifier = "missing_app"
    plugin = webhook_plugin()

    # when & then
    with pytest.raises(TaxDataError, match="Configured tax app doesn't exist."):
        plugin.get_taxes_for_order(order, app_identifier, None)


def test_get_taxes_for_order_with_app_identifier_webhook_is_missing(
    order, webhook_plugin, app
):
    # given
    plugin = webhook_plugin()

    # when & then
    with pytest.raises(
        TaxDataError,
        match="Configured tax app's webhook for taxes calculation doesn't exists.",
    ):
        plugin.get_taxes_for_order(order, app.identifier, None)


@mock.patch("saleor.order.calculations.fetch_order_prices_if_expired")
@mock.patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
@mock.patch(
    "saleor.webhook.transport.synchronous.transport.generate_payload_from_subscription"
)
def test_get_taxes_for_order_with_app_identifier_invalid_response(
    mock_generate_payload,
    mock_request,
    mock_fetch,
    webhook_plugin,
    tax_data_response_factory,
    order,
    tax_app,
):
    # given
    subscription_query = "subscription{event{... on CalculateTaxes{taxBase{currency}}}}"
    expected_payload = {"taxBase": {"currency": "USD"}}
    # mock returning invalid data - tax_rate above 100
    mock_request.return_value = tax_data_response_factory(shipping_tax_rate=120)
    mock_generate_payload.return_value = expected_payload
    plugin = webhook_plugin()
    webhook = tax_app.webhooks.get(name="tax-webhook-1")
    webhook.subscription_query = subscription_query
    webhook.save(update_fields=["subscription_query"])
    app_identifier = tax_app.identifier

    # when & then
    with pytest.raises(TaxDataError):
        plugin.get_taxes_for_order(order, app_identifier, None)


@freeze_time()
@mock.patch("saleor.order.calculations.fetch_order_prices_if_expired")
@mock.patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
@mock.patch(
    "saleor.webhook.transport.synchronous.transport.generate_payload_from_subscription"
)
def test_get_taxes_for_order_with_app_identifier(
    mock_generate_payload,
    mock_request,
    mock_fetch,
    webhook_plugin,
    tax_data_response,
    order,
    tax_app,
):
    # given
    subscription_query = "subscription{event{... on CalculateTaxes{taxBase{currency}}}}"
    expected_payload = {"taxBase": {"currency": "USD"}}
    mock_request.return_value = tax_data_response
    mock_generate_payload.return_value = expected_payload
    plugin = webhook_plugin()
    webhook = tax_app.webhooks.get(name="tax-webhook-1")
    webhook.subscription_query = subscription_query
    webhook.save(update_fields=["subscription_query"])
    app_identifier = tax_app.identifier

    # when
    tax_data = plugin.get_taxes_for_order(order, app_identifier, None)

    # then
    mock_generate_payload.assert_called_once_with(
        event_type=WebhookEventSyncType.ORDER_CALCULATE_TAXES,
        subscribable_object=order,
        subscription_query=subscription_query,
        request=ANY,  # SaleorContext,
        app=tax_app,
    )
    mock_request.assert_called_once()
    assert not EventDelivery.objects.exists()

    delivery = mock_request.mock_calls[0].args[0]
    assert delivery.payload.get_payload() == json.dumps(expected_payload)
    assert delivery.status == EventDeliveryStatus.PENDING
    assert delivery.event_type == WebhookEventSyncType.ORDER_CALCULATE_TAXES
    assert delivery.webhook == webhook
    mock_fetch.assert_not_called()
    assert tax_data == parse_tax_data(tax_data_response, order.lines.count())


@freeze_time()
@mock.patch("saleor.order.calculations.fetch_order_prices_if_expired")
@mock.patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
@mock.patch(
    "saleor.webhook.transport.synchronous.transport.generate_payload_from_subscription"
)
def test_get_taxes_for_order_with_app_identifier_empty_response(
    mock_generate_payload,
    mock_request,
    mock_fetch,
    webhook_plugin,
    tax_data_response,
    order,
    tax_app,
):
    # given
    mock_request.return_value = None
    subscription_query = "subscription{event{... on CalculateTaxes{taxBase{currency}}}}"
    expected_payload = {"taxBase": {"currency": "USD"}}
    mock_generate_payload.return_value = expected_payload
    plugin = webhook_plugin()
    webhook = tax_app.webhooks.get(name="tax-webhook-1")
    webhook.subscription_query = subscription_query
    webhook.save(update_fields=["subscription_query"])
    app_identifier = tax_app.identifier

    # when & then
    with pytest.raises(TaxDataError):
        plugin.get_taxes_for_order(order, app_identifier, None)


@freeze_time()
@mock.patch("saleor.checkout.calculations.fetch_checkout_data")
@mock.patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
@mock.patch(
    "saleor.webhook.transport.synchronous.transport.generate_payload_from_subscription"
)
def test_get_taxes_for_checkout_with_app_identifier_empty_response(
    mock_generate_payload,
    mock_request,
    mock_fetch,
    webhook_plugin,
    tax_data_response,
    checkout,
    tax_app,
):
    # given
    subscription_query = "subscription{event{... on CalculateTaxes{taxBase{currency}}}}"
    expected_payload = {"taxBase": {"currency": "USD"}}
    checkout_info = fetch_checkout_info(
        checkout, [], get_plugins_manager(allow_replica=False)
    )
    mock_request.return_value = None
    mock_generate_payload.return_value = expected_payload
    plugin = webhook_plugin()
    webhook = tax_app.webhooks.get(name="tax-webhook-1")
    webhook.subscription_query = subscription_query
    webhook.save(update_fields=["subscription_query"])
    app_identifier = tax_app.identifier

    # when & then
    with pytest.raises(TaxDataError):
        plugin.get_taxes_for_checkout(checkout_info, [], app_identifier, None)
