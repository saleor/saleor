import json
from unittest.mock import ANY, patch

import pytest
from freezegun import freeze_time

from ....core import EventDeliveryStatus
from ....core.models import EventDelivery
from ....core.taxes import TaxDataError
from ....graphql.webhook.subscription_payload import (
    generate_payload_promise_from_subscription,
)
from ....tax.webhooks.parser import parse_tax_data
from ....webhook.event_types import WebhookEventSyncType
from ...webhooks.order_calculate_taxes import (
    generate_order_payload_for_tax_calculation,
    get_taxes,
)


@freeze_time()
@patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
def test_get_taxes_for_order(
    mock_request,
    tax_data_response,
    order,
    tax_app,
):
    # given
    mock_request.return_value = tax_data_response

    app_identifier = None
    webhook = tax_app.webhooks.get(name="tax-webhook-1")
    webhook.subscription_query = None
    webhook.save(update_fields=["subscription_query"])

    # when
    tax_data = get_taxes(
        order=order,
        lines=order.lines.all(),
        app_identifier=app_identifier,
        requestor=None,
    ).get()

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

    assert tax_data == parse_tax_data(
        WebhookEventSyncType.ORDER_CALCULATE_TAXES,
        tax_data_response,
        order.lines.count(),
    )


@freeze_time()
@patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
def test_get_taxes_for_order_with_sync_subscription(
    mock_request,
    tax_data_response,
    order,
    tax_app,
):
    # given
    mock_request.return_value = tax_data_response
    webhook = tax_app.webhooks.get(name="tax-webhook-1")
    webhook.subscription_query = (
        "subscription{event{... on CalculateTaxes{taxBase{currency}}}}"
    )
    webhook.save(update_fields=["subscription_query"])
    app_identifier = None

    # when
    tax_data = get_taxes(
        order=order,
        lines=order.lines.all(),
        app_identifier=app_identifier,
        requestor=None,
    ).get()

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
    assert tax_data == parse_tax_data(
        WebhookEventSyncType.ORDER_CALCULATE_TAXES,
        tax_data_response,
        order.lines.count(),
    )


def test_get_taxes_for_order_with_app_identifier_app_missing(order):
    # given
    app_identifier = "missing_app"

    # when & then
    with pytest.raises(TaxDataError, match="Configured tax app doesn't exist."):
        get_taxes(order, order.lines.all(), app_identifier, None).get()


def test_get_taxes_for_order_with_app_identifier_webhook_is_missing(order, app):
    with pytest.raises(
        TaxDataError,
        match="Configured tax app's webhook for taxes calculation doesn't exists.",
    ):
        get_taxes(order, order.lines.all(), app.identifier, None).get()


@patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
def test_get_taxes_for_order_with_app_identifier_invalid_response(
    mock_request,
    order,
    tax_app,
    tax_data_response_factory,
):
    # given
    subscription_query = "subscription{event{... on CalculateTaxes{taxBase{currency}}}}"
    mock_request.return_value = tax_data_response_factory(shipping_tax_rate=-10)

    webhook = tax_app.webhooks.get(name="tax-webhook-1")
    webhook.subscription_query = subscription_query
    webhook.save(update_fields=["subscription_query"])
    app_identifier = tax_app.identifier

    # when & then
    with pytest.raises(TaxDataError):
        get_taxes(order, order.lines.all(), app_identifier, None).get()


@patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
def test_get_taxes_for_order_with_app_identifier_empty_response(
    mock_request,
    order,
    tax_app,
):
    # given
    subscription_query = "subscription{event{... on CalculateTaxes{taxBase{currency}}}}"
    mock_request.return_value = None

    webhook = tax_app.webhooks.get(name="tax-webhook-1")
    webhook.subscription_query = subscription_query
    webhook.save(update_fields=["subscription_query"])
    app_identifier = tax_app.identifier

    # when & then
    with pytest.raises(TaxDataError):
        get_taxes(order, order.lines.all(), app_identifier, None).get()


@freeze_time()
@patch(
    "saleor.webhook.transport.synchronous.transport.generate_payload_promise_from_subscription",
    wraps=generate_payload_promise_from_subscription,
)
@patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
def test_get_taxes_for_order_with_app_identifier(
    mock_request,
    mock_generate_payload,
    tax_data_response,
    order,
    tax_app,
):
    # given
    subscription_query = "subscription{event{... on CalculateTaxes{taxBase{currency}}}}"
    expected_payload = {"taxBase": {"currency": "USD"}}
    mock_request.return_value = tax_data_response

    webhook = tax_app.webhooks.get(name="tax-webhook-1")
    webhook.subscription_query = subscription_query
    webhook.save(update_fields=["subscription_query"])
    app_identifier = tax_app.identifier

    # when
    tax_data = get_taxes(order, order.lines.all(), app_identifier, None).get()

    # then
    mock_generate_payload.assert_called_once_with(
        event_type=WebhookEventSyncType.ORDER_CALCULATE_TAXES,
        subscribable_object=order,
        subscription_query=subscription_query,
        request=ANY,
    )
    mock_request.assert_called_once()
    assert not EventDelivery.objects.exists()

    delivery = mock_request.mock_calls[0].args[0]
    assert delivery.payload.get_payload() == json.dumps(expected_payload)
    assert delivery.status == EventDeliveryStatus.PENDING
    assert delivery.event_type == WebhookEventSyncType.ORDER_CALCULATE_TAXES
    assert delivery.webhook == webhook
    assert tax_data == parse_tax_data(
        WebhookEventSyncType.ORDER_CALCULATE_TAXES,
        tax_data_response,
        order.lines.count(),
    )


@freeze_time()
@patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
def test_get_taxes_for_order_sets_issuing_principal(
    mock_request, tax_data_response, order, tax_app, customer_user
):
    # given
    mock_request.return_value = tax_data_response
    webhook = tax_app.webhooks.get(name="tax-webhook-1")
    webhook.subscription_query = "subscription{event{issuingPrincipal {__typename}}}"
    webhook.save(update_fields=["subscription_query"])
    app_identifier = tax_app.identifier

    # when
    tax_data = get_taxes(
        order=order,
        lines=order.lines.all(),
        app_identifier=app_identifier,
        requestor=customer_user,
    ).get()

    # then
    mock_request.assert_called_once()
    assert not EventDelivery.objects.exists()

    delivery = mock_request.mock_calls[0].args[0]
    assert delivery.payload.get_payload() == json.dumps(
        {"issuingPrincipal": {"__typename": "User"}}
    )
    assert delivery.status == EventDeliveryStatus.PENDING
    assert delivery.event_type == WebhookEventSyncType.ORDER_CALCULATE_TAXES
    assert delivery.webhook == webhook
    assert tax_data == parse_tax_data(
        WebhookEventSyncType.ORDER_CALCULATE_TAXES,
        tax_data_response,
        order.lines.count(),
    )
