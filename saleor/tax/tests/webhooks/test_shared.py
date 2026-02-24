import json
from unittest import mock

import graphene
import pytest

from saleor.core.taxes import TaxDataError

from ....core import EventDeliveryStatus
from ....core.models import EventDelivery
from ....webhook.event_types import WebhookEventSyncType
from ....webhook.models import Webhook, WebhookEvent

# from ....webhook.transport.synchronous import trigger_taxes_all_webhooks_sync
from ...webhooks.parser import parse_tax_data
from ...webhooks.shared import (
    get_taxes,
    get_taxes_for_app_identifier,
    get_taxes_from_all_webhooks,
)

TAX_SUBSCRIPTION_QUERY = """
    subscription {
      event {
        ... on CalculateTaxes {
          taxBase {
            sourceObject {
              ...on Order{
                id
                lines{
                  id
                }
              }
            }
          }
        }
      }
    }
"""


@pytest.fixture
def tax_webhooks(tax_app):
    webhooks = [
        Webhook(
            name=f"Tax order webhook no {i}",
            app=tax_app,
            target_url=f"https://127.0.0.1/tax-order-{i}",
        )
        for i in range(3)
    ]
    webhooks = Webhook.objects.bulk_create(webhooks)
    WebhookEvent.objects.bulk_create(
        WebhookEvent(
            event_type=WebhookEventSyncType.ORDER_CALCULATE_TAXES,
            webhook=webhook,
        )
        for webhook in webhooks
    )
    return webhooks


@mock.patch(
    "saleor.tax.webhooks.shared.get_taxes_from_all_webhooks",
    wraps=get_taxes_from_all_webhooks,
)
@mock.patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
def test_get_taxes_from_all_webhooks(
    mocked_send_webhook_request_sync,
    mocked_get_taxes_from_all_webhooks,
    tax_app,
    tax_data_response,
    tax_configuration_tax_app,
    order_with_lines,
    customer_user,
):
    # given
    tax_configuration_tax_app.tax_app_id = None
    tax_configuration_tax_app.save(update_fields=["tax_app_id"])

    mocked_send_webhook_request_sync.return_value = tax_data_response

    event_type = WebhookEventSyncType.ORDER_CALCULATE_TAXES
    data = '{"key": "value"}'

    webhook = tax_app.webhooks.get(name="tax-webhook-1")
    webhook.subscription_query = TAX_SUBSCRIPTION_QUERY
    webhook.save(update_fields=["subscription_query"])

    lines_count = len(tax_data_response["lines"])

    # when
    tax_data = get_taxes(
        taxable_object=order_with_lines,
        event_type=event_type,
        app_identifier=None,
        static_payload=data,
        lines_count=lines_count,
        requestor=customer_user,
    ).get()

    # then
    mocked_send_webhook_request_sync.assert_called_once()
    mocked_get_taxes_from_all_webhooks.assert_called_once()

    assert not EventDelivery.objects.exists()
    delivery = mocked_send_webhook_request_sync.mock_calls[0].args[0]

    assert json.loads(delivery.payload.get_payload()) == {
        "taxBase": {
            "sourceObject": {
                "id": graphene.Node.to_global_id("Order", order_with_lines.pk),
                "lines": [
                    {"id": graphene.Node.to_global_id("OrderLine", line.pk)}
                    for line in order_with_lines.lines.all()
                ],
            }
        }
    }
    assert delivery.status == EventDeliveryStatus.PENDING
    assert delivery.event_type == event_type
    assert delivery.webhook == webhook
    assert tax_data == parse_tax_data(event_type, tax_data_response, lines_count)


@mock.patch(
    "saleor.tax.webhooks.shared.get_taxes_from_all_webhooks",
    wraps=get_taxes_from_all_webhooks,
)
@mock.patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
def test_get_taxes_from_all_webhooks_multiple_webhooks(
    mocked_send_webhook_request_sync,
    mocked_get_taxes_from_all_webhooks,
    tax_app,
    tax_data_response,
    tax_configuration_tax_app,
    order_with_lines,
    customer_user,
    tax_webhooks,
):
    # given
    tax_configuration_tax_app.tax_app_id = None
    tax_configuration_tax_app.save(update_fields=["tax_app_id"])

    mocked_send_webhook_request_sync.side_effect = [None, {}, tax_data_response, None]

    event_type = WebhookEventSyncType.ORDER_CALCULATE_TAXES
    data = '{"key": "value"}'
    webhook = tax_app.webhooks.get(name="tax-webhook-1")
    webhook.subscription_query = TAX_SUBSCRIPTION_QUERY
    webhook.save(update_fields=["subscription_query"])
    lines_count = len(tax_data_response["lines"])

    # when
    tax_data = get_taxes(
        taxable_object=order_with_lines,
        event_type=event_type,
        app_identifier=None,
        static_payload=data,
        lines_count=lines_count,
        requestor=customer_user,
    ).get()

    # then
    assert mocked_send_webhook_request_sync.call_count == 4
    assert mocked_get_taxes_from_all_webhooks.call_count == 1

    assert not EventDelivery.objects.exists()
    delivery = mocked_send_webhook_request_sync.mock_calls[0].args[0]

    assert json.loads(delivery.payload.get_payload()) == {
        "taxBase": {
            "sourceObject": {
                "id": graphene.Node.to_global_id("Order", order_with_lines.pk),
                "lines": [
                    {"id": graphene.Node.to_global_id("OrderLine", line.pk)}
                    for line in order_with_lines.lines.all()
                ],
            }
        }
    }
    assert delivery.status == EventDeliveryStatus.PENDING
    assert delivery.event_type == event_type
    assert delivery.webhook == webhook
    assert tax_data == parse_tax_data(event_type, tax_data_response, lines_count)


@mock.patch(
    "saleor.tax.webhooks.shared.get_taxes_from_all_webhooks",
    wraps=get_taxes_from_all_webhooks,
)
@mock.patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
def test_get_taxes_from_all_webhooks_multiple_invalid_webhooks(
    mocked_send_webhook_request_sync,
    mocked_get_taxes_from_all_webhooks,
    tax_app,
    tax_data_response,
    tax_configuration_tax_app,
    order_with_lines,
    customer_user,
    tax_webhooks,
):
    # given
    tax_configuration_tax_app.tax_app_id = None
    tax_configuration_tax_app.save(update_fields=["tax_app_id"])

    mocked_send_webhook_request_sync.side_effect = [None, {}, None, None]

    event_type = WebhookEventSyncType.ORDER_CALCULATE_TAXES
    data = '{"key": "value"}'
    webhook = tax_app.webhooks.get(name="tax-webhook-1")
    webhook.subscription_query = TAX_SUBSCRIPTION_QUERY
    webhook.save(update_fields=["subscription_query"])
    lines_count = len(tax_data_response["lines"])

    # when
    tax_data = get_taxes(
        taxable_object=order_with_lines,
        event_type=event_type,
        app_identifier=None,
        static_payload=data,
        lines_count=lines_count,
        requestor=customer_user,
    ).get()

    # then
    assert mocked_send_webhook_request_sync.call_count == 4
    assert mocked_get_taxes_from_all_webhooks.call_count == 1

    assert not EventDelivery.objects.exists()
    delivery = mocked_send_webhook_request_sync.mock_calls[0].args[0]

    assert json.loads(delivery.payload.get_payload()) == {
        "taxBase": {
            "sourceObject": {
                "id": graphene.Node.to_global_id("Order", order_with_lines.pk),
                "lines": [
                    {"id": graphene.Node.to_global_id("OrderLine", line.pk)}
                    for line in order_with_lines.lines.all()
                ],
            }
        }
    }
    assert delivery.status == EventDeliveryStatus.PENDING
    assert delivery.event_type == event_type
    assert delivery.webhook == webhook
    assert tax_data is None


@mock.patch(
    "saleor.tax.webhooks.shared.get_taxes_for_app_identifier",
    wraps=get_taxes_for_app_identifier,
)
@mock.patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
def test_get_taxes_for_app_identifier(
    mocked_send_webhook_request_sync,
    mocked_get_taxes_for_app_identifier,
    tax_app,
    tax_data_response,
    tax_configuration_tax_app,
    order_with_lines,
    customer_user,
):
    # given
    tax_configuration_tax_app.tax_app_id = tax_app.identifier
    tax_configuration_tax_app.save(update_fields=["tax_app_id"])

    mocked_send_webhook_request_sync.return_value = tax_data_response

    event_type = WebhookEventSyncType.ORDER_CALCULATE_TAXES
    data = '{"key": "value"}'

    webhook = tax_app.webhooks.get(name="tax-webhook-1")
    webhook.subscription_query = TAX_SUBSCRIPTION_QUERY
    webhook.save(update_fields=["subscription_query"])

    lines_count = len(tax_data_response["lines"])

    # when
    tax_data = get_taxes(
        taxable_object=order_with_lines,
        event_type=event_type,
        app_identifier=tax_app.identifier,
        static_payload=data,
        lines_count=lines_count,
        requestor=customer_user,
    ).get()

    # then
    mocked_send_webhook_request_sync.assert_called_once()
    mocked_get_taxes_for_app_identifier.assert_called_once()

    assert not EventDelivery.objects.exists()
    delivery = mocked_send_webhook_request_sync.mock_calls[0].args[0]

    assert json.loads(delivery.payload.get_payload()) == {
        "taxBase": {
            "sourceObject": {
                "id": graphene.Node.to_global_id("Order", order_with_lines.pk),
                "lines": [
                    {"id": graphene.Node.to_global_id("OrderLine", line.pk)}
                    for line in order_with_lines.lines.all()
                ],
            }
        }
    }
    assert delivery.status == EventDeliveryStatus.PENDING
    assert delivery.event_type == event_type
    assert delivery.webhook == webhook
    assert tax_data == parse_tax_data(event_type, tax_data_response, lines_count)


@mock.patch(
    "saleor.tax.webhooks.shared.get_taxes_for_app_identifier",
    wraps=get_taxes_for_app_identifier,
)
@mock.patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
def test_get_taxes_for_app_identifier_multiple_webhooks(
    mocked_send_webhook_request_sync,
    mocked_get_taxes_for_app_identifier,
    tax_app,
    tax_data_response,
    tax_configuration_tax_app,
    order_with_lines,
    customer_user,
    tax_webhooks,
):
    # given
    tax_configuration_tax_app.tax_app_id = tax_app.identifier
    tax_configuration_tax_app.save(update_fields=["tax_app_id"])

    mocked_send_webhook_request_sync.return_value = tax_data_response

    event_type = WebhookEventSyncType.ORDER_CALCULATE_TAXES
    data = '{"key": "value"}'
    webhook = tax_app.webhooks.get(name="tax-webhook-1")
    webhook.subscription_query = TAX_SUBSCRIPTION_QUERY
    webhook.save(update_fields=["subscription_query"])
    lines_count = len(tax_data_response["lines"])

    # when
    tax_data = get_taxes(
        taxable_object=order_with_lines,
        event_type=event_type,
        app_identifier=tax_app.identifier,
        static_payload=data,
        lines_count=lines_count,
        requestor=customer_user,
    ).get()

    # then
    mocked_send_webhook_request_sync.assert_called_once()
    mocked_get_taxes_for_app_identifier.assert_called_once()

    assert not EventDelivery.objects.exists()
    delivery = mocked_send_webhook_request_sync.mock_calls[0].args[0]

    assert json.loads(delivery.payload.get_payload()) == {
        "taxBase": {
            "sourceObject": {
                "id": graphene.Node.to_global_id("Order", order_with_lines.pk),
                "lines": [
                    {"id": graphene.Node.to_global_id("OrderLine", line.pk)}
                    for line in order_with_lines.lines.all()
                ],
            }
        }
    }
    assert delivery.status == EventDeliveryStatus.PENDING
    assert delivery.event_type == event_type
    assert delivery.webhook == webhook
    assert tax_data == parse_tax_data(event_type, tax_data_response, lines_count)


@mock.patch(
    "saleor.tax.webhooks.shared.get_taxes_for_app_identifier",
    wraps=get_taxes_for_app_identifier,
)
@mock.patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
def test_get_taxes_for_app_identifier_invalid_response(
    mocked_send_webhook_request_sync,
    mocked_get_taxes_for_app_identifier,
    tax_app,
    tax_data_response,
    tax_configuration_tax_app,
    order_with_lines,
    customer_user,
    tax_webhooks,
):
    # given
    tax_configuration_tax_app.tax_app_id = None
    tax_configuration_tax_app.save(update_fields=["tax_app_id"])

    mocked_send_webhook_request_sync.return_value = None

    event_type = WebhookEventSyncType.ORDER_CALCULATE_TAXES
    data = '{"key": "value"}'
    webhook = tax_app.webhooks.get(name="tax-webhook-1")
    webhook.subscription_query = TAX_SUBSCRIPTION_QUERY
    webhook.save(update_fields=["subscription_query"])
    lines_count = len(tax_data_response["lines"])

    # when
    with pytest.raises(TaxDataError):
        get_taxes(
            taxable_object=order_with_lines,
            event_type=event_type,
            app_identifier=tax_app.identifier,
            static_payload=data,
            lines_count=lines_count,
            requestor=customer_user,
        ).get()

    # then
    assert mocked_send_webhook_request_sync.call_count == 1
    assert mocked_get_taxes_for_app_identifier.call_count == 1

    assert not EventDelivery.objects.exists()
    delivery = mocked_send_webhook_request_sync.mock_calls[0].args[0]

    assert json.loads(delivery.payload.get_payload()) == {
        "taxBase": {
            "sourceObject": {
                "id": graphene.Node.to_global_id("Order", order_with_lines.pk),
                "lines": [
                    {"id": graphene.Node.to_global_id("OrderLine", line.pk)}
                    for line in order_with_lines.lines.all()
                ],
            }
        }
    }
    assert delivery.status == EventDeliveryStatus.PENDING
    assert delivery.event_type == event_type
    assert delivery.webhook == webhook
