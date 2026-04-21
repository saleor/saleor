import json
from unittest import mock
from unittest.mock import ANY

import pytest
from promise import Promise

from ....checkout.fetch import fetch_checkout_info, fetch_checkout_lines
from ....checkout.webhooks import calculate_taxes as checkout_calculate_taxes
from ....core import EventDeliveryStatus
from ....core.models import EventDelivery
from ....core.taxes import TaxDataError
from ....plugins.manager import get_plugins_manager
from ....tax.webhooks.parser import parse_tax_data
from ....webhook.event_types import WebhookEventSyncType
from ....webhook.models import Webhook, WebhookEvent


@mock.patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
def test_get_taxes_no_permission(
    mock_request,
    checkout,
):
    # given
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(
        checkout, lines, get_plugins_manager(allow_replica=False)
    )
    app_identifier = None

    # when
    tax_data = checkout_calculate_taxes.get_taxes(
        checkout_info, lines, app_identifier
    ).get()

    # then
    assert mock_request.call_count == 0
    assert tax_data is None


@mock.patch("saleor.checkout.calculations.fetch_checkout_data")
@mock.patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
@mock.patch(
    "saleor.webhook.transport.synchronous.transport.generate_payload_promise_from_subscription"
)
def test_get_taxes_with_sync_subscription(
    mock_generate_payload,
    mock_request,
    mock_fetch,
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
    mock_generate_payload.return_value = Promise.resolve(expected_payload)
    webhook = tax_app.webhooks.get(name="tax-webhook-1")
    webhook.subscription_query = subscription_query
    webhook.save(update_fields=["subscription_query"])
    app_identifier = None

    # when
    tax_data = checkout_calculate_taxes.get_taxes(
        checkout_info, [], app_identifier
    ).get()

    # then
    mock_generate_payload.assert_called_once_with(
        event_type=WebhookEventSyncType.CHECKOUT_CALCULATE_TAXES,
        subscribable_object=checkout,
        subscription_query=subscription_query,
        request=ANY,  # SaleorContext,
    )
    mock_request.assert_called_once()
    assert not EventDelivery.objects.exists()

    delivery = mock_request.mock_calls[0].args[0]
    assert delivery.payload.get_payload() == json.dumps(expected_payload)
    assert delivery.status == EventDeliveryStatus.PENDING
    assert delivery.event_type == WebhookEventSyncType.CHECKOUT_CALCULATE_TAXES
    assert delivery.webhook == webhook
    mock_fetch.assert_not_called()
    assert tax_data == parse_tax_data(
        WebhookEventSyncType.CHECKOUT_CALCULATE_TAXES,
        tax_data_response,
        checkout.lines.count(),
    )


def test_get_taxes_with_app_identifier_app_missing(checkout_info):
    # given
    app_identifier = "missing_app"

    # when & then
    with pytest.raises(TaxDataError, match="Configured tax app doesn't exist."):
        checkout_calculate_taxes.get_taxes(
            checkout_info, checkout_info.lines, app_identifier
        ).get()


def test_get_taxes_with_app_identifier_webhook_is_missing(checkout_info, app):
    # when & then
    with pytest.raises(
        TaxDataError,
        match="Configured tax app's webhook for taxes calculation doesn't exists.",
    ):
        checkout_calculate_taxes.get_taxes(
            checkout_info, checkout_info.lines, app.identifier
        ).get()


@mock.patch("saleor.checkout.calculations.fetch_checkout_data")
@mock.patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
@mock.patch(
    "saleor.webhook.transport.synchronous.transport.generate_payload_promise_from_subscription"
)
def test_get_taxes_with_app_identifier_invalid_response(
    mock_generate_payload,
    mock_request,
    mock_fetch,
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
    mock_request.return_value = tax_data_response_factory(shipping_tax_rate=-10)
    mock_generate_payload.return_value = Promise.resolve(expected_payload)
    webhook = tax_app.webhooks.get(name="tax-webhook-1")
    webhook.subscription_query = subscription_query
    webhook.save(update_fields=["subscription_query"])
    app_identifier = tax_app.identifier

    # when
    with pytest.raises(TaxDataError):
        checkout_calculate_taxes.get_taxes(checkout_info, [], app_identifier).get()


@mock.patch("saleor.checkout.calculations.fetch_checkout_data")
@mock.patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
@mock.patch(
    "saleor.webhook.transport.synchronous.transport.generate_payload_promise_from_subscription"
)
def test_get_taxes_with_app_identifier(
    mock_generate_payload,
    mock_request,
    mock_fetch,
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
    mock_generate_payload.return_value = Promise.resolve(expected_payload)
    webhook = tax_app.webhooks.get(name="tax-webhook-1")
    webhook.subscription_query = subscription_query
    webhook.save(update_fields=["subscription_query"])
    app_identifier = tax_app.identifier

    # when
    tax_data = checkout_calculate_taxes.get_taxes(
        checkout_info, [], app_identifier
    ).get()

    # then
    mock_generate_payload.assert_called_once_with(
        event_type=WebhookEventSyncType.CHECKOUT_CALCULATE_TAXES,
        subscribable_object=checkout,
        subscription_query=subscription_query,
        request=ANY,  # SaleorContext,
    )
    mock_request.assert_called_once()
    assert not EventDelivery.objects.exists()

    delivery = mock_request.mock_calls[0].args[0]
    assert delivery.payload.get_payload() == json.dumps(expected_payload)
    assert delivery.status == EventDeliveryStatus.PENDING
    assert delivery.event_type == WebhookEventSyncType.CHECKOUT_CALCULATE_TAXES
    assert delivery.webhook == webhook
    mock_fetch.assert_not_called()
    assert tax_data == parse_tax_data(
        WebhookEventSyncType.CHECKOUT_CALCULATE_TAXES,
        tax_data_response,
        checkout.lines.count(),
    )


@mock.patch("saleor.checkout.calculations.fetch_checkout_data")
@mock.patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
@mock.patch(
    "saleor.webhook.transport.synchronous.transport.generate_payload_promise_from_subscription"
)
def test_get_taxes_with_app_identifier_empty_response(
    mock_generate_payload,
    mock_request,
    mock_fetch,
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
    mock_generate_payload.return_value = Promise.resolve(expected_payload)
    webhook = tax_app.webhooks.get(name="tax-webhook-1")
    webhook.subscription_query = subscription_query
    webhook.save(update_fields=["subscription_query"])
    app_identifier = tax_app.identifier

    # when & then
    with pytest.raises(TaxDataError):
        checkout_calculate_taxes.get_taxes(checkout_info, [], app_identifier).get()


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
