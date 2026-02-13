from unittest import mock
from unittest.mock import MagicMock

import pytest

from ...checkout.models import Checkout
from ...core import EventDeliveryStatus
from ...core.models import EventDelivery
from ..event_types import WebhookEventSyncType
from ..models import Webhook, WebhookEvent
from ..transport.synchronous import trigger_taxes_all_webhooks_sync
from ..transport.taxes import parse_tax_data


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


@mock.patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
def test_trigger_tax_webhook_sync(
    mock_request,
    tax_app,
    tax_data_response,
):
    # given
    mock_request.return_value = tax_data_response
    event_type = WebhookEventSyncType.CHECKOUT_CALCULATE_TAXES
    data = '{"key": "value"}'
    webhook = tax_app.webhooks.get(name="tax-webhook-1")
    webhook.subscription_query = None
    webhook.save(update_fields=["subscription_query"])
    lines_count = len(tax_data_response["lines"])

    # when
    tax_data = trigger_taxes_all_webhooks_sync(event_type, lambda: data, lines_count)

    # then
    mock_request.assert_called_once()
    assert not EventDelivery.objects.exists()
    delivery = mock_request.mock_calls[0].args[0]

    assert delivery.payload.get_payload() == data
    assert delivery.status == EventDeliveryStatus.PENDING
    assert delivery.event_type == event_type
    assert delivery.webhook == webhook
    assert tax_data == parse_tax_data(tax_data_response, lines_count)


@mock.patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
def test_trigger_tax_webhook_sync_multiple_webhooks_first(
    mock_request,
    tax_checkout_webhooks,
    tax_data_response,
):
    # given
    mock_request.side_effect = [tax_data_response, {}, {}]
    event_type = WebhookEventSyncType.CHECKOUT_CALCULATE_TAXES
    data = '{"key": "value"}'
    lines_count = len(tax_data_response["lines"])

    # when
    tax_data = trigger_taxes_all_webhooks_sync(event_type, lambda: data, lines_count)

    # then
    successful_webhook = tax_checkout_webhooks[0]
    mock_request.assert_called_once()
    assert not EventDelivery.objects.exists()
    delivery = mock_request.mock_calls[0].args[0]
    assert delivery.payload.get_payload() == data
    assert delivery.status == EventDeliveryStatus.PENDING
    assert delivery.event_type == event_type
    assert delivery.webhook == successful_webhook
    assert tax_data == parse_tax_data(tax_data_response, lines_count)


@mock.patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
def test_trigger_tax_webhook_sync_multiple_webhooks_last(
    mock_request,
    tax_checkout_webhooks,
    tax_data_response,
):
    # given
    mock_request.side_effect = [{}, {}, tax_data_response]
    event_type = WebhookEventSyncType.CHECKOUT_CALCULATE_TAXES
    data = '{"key": "value"}'
    lines_count = len(tax_data_response["lines"])

    # when
    tax_data = trigger_taxes_all_webhooks_sync(event_type, lambda: data, lines_count)

    # then
    assert mock_request.call_count == 3
    assert not EventDelivery.objects.exists()

    for call, webhook in zip(
        mock_request.mock_calls, tax_checkout_webhooks, strict=False
    ):
        delivery = call.args[0]
        assert delivery.status == EventDeliveryStatus.PENDING
        assert delivery.event_type == event_type
        assert delivery.payload.get_payload() == data
        assert delivery.webhook == webhook

    assert tax_data == parse_tax_data(tax_data_response, lines_count)


@mock.patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
def test_trigger_tax_webhook_sync_invalid_webhooks(
    mock_request,
    tax_checkout_webhooks,
    tax_data_response,
):
    # given
    mock_request.return_value = {}
    event_type = WebhookEventSyncType.CHECKOUT_CALCULATE_TAXES
    data = '{"key": "value"}'

    # when
    tax_data = trigger_taxes_all_webhooks_sync(event_type, lambda: data, 0)

    # then
    assert mock_request.call_count == len(tax_checkout_webhooks)
    assert tax_data is None


@pytest.fixture
def tax_checkout_webhook_with_defer(tax_app):
    tax_app.webhooks.all().delete()
    webhook = Webhook.objects.create(
        name="Tax webhook with defer",
        app=tax_app,
        target_url="https://www.example.com/tax-deferred",
        defer_if_conditions=["ADDRESS_MISSING"],
    )
    WebhookEvent.objects.create(
        event_type=WebhookEventSyncType.CHECKOUT_CALCULATE_TAXES,
        webhook=webhook,
    )
    return webhook


@mock.patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
def test_trigger_tax_webhook_sync_skips_webhook_when_defer_condition_met(
    mock_request,
    tax_checkout_webhook_with_defer,
    tax_data_response,
):
    # given
    event_type = WebhookEventSyncType.CHECKOUT_CALCULATE_TAXES
    data = '{"key": "value"}'
    lines_count = len(tax_data_response["lines"])
    subscribable_object = MagicMock(spec=Checkout)
    subscribable_object.is_shipping_required.return_value = True
    subscribable_object.shipping_address_id = None

    # when
    tax_data = trigger_taxes_all_webhooks_sync(
        event_type,
        lambda: data,
        lines_count,
        subscribable_object=subscribable_object,
    )

    # then
    mock_request.assert_not_called()
    assert tax_data is None


@mock.patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
def test_trigger_tax_webhook_sync_calls_webhook_when_defer_condition_not_met(
    mock_request,
    tax_checkout_webhook_with_defer,
    tax_data_response,
):
    # given
    mock_request.return_value = tax_data_response
    event_type = WebhookEventSyncType.CHECKOUT_CALCULATE_TAXES
    data = '{"key": "value"}'
    lines_count = len(tax_data_response["lines"])
    subscribable_object = MagicMock(spec=Checkout)
    subscribable_object.is_shipping_required.return_value = True
    subscribable_object.shipping_address_id = 1

    # when
    tax_data = trigger_taxes_all_webhooks_sync(
        event_type,
        lambda: data,
        lines_count,
        subscribable_object=subscribable_object,
    )

    # then
    mock_request.assert_called_once()
    assert tax_data == parse_tax_data(tax_data_response, lines_count)


@mock.patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
def test_trigger_tax_webhook_sync_skips_deferred_but_tries_next_webhook(
    mock_request,
    tax_app,
    tax_data_response,
):
    # given - two webhooks: first has defer condition, second does not
    tax_app.webhooks.all().delete()
    deferred_webhook = Webhook.objects.create(
        name="Deferred tax webhook",
        app=tax_app,
        target_url="https://www.example.com/tax-deferred",
        defer_if_conditions=["ADDRESS_MISSING"],
    )
    WebhookEvent.objects.create(
        event_type=WebhookEventSyncType.CHECKOUT_CALCULATE_TAXES,
        webhook=deferred_webhook,
    )
    normal_webhook = Webhook.objects.create(
        name="Normal tax webhook",
        app=tax_app,
        target_url="https://www.example.com/tax-normal",
        defer_if_conditions=[],
    )
    WebhookEvent.objects.create(
        event_type=WebhookEventSyncType.CHECKOUT_CALCULATE_TAXES,
        webhook=normal_webhook,
    )

    mock_request.return_value = tax_data_response
    event_type = WebhookEventSyncType.CHECKOUT_CALCULATE_TAXES
    data = '{"key": "value"}'
    lines_count = len(tax_data_response["lines"])

    subscribable_object = MagicMock(spec=Checkout)
    subscribable_object.is_shipping_required.return_value = True
    subscribable_object.shipping_address_id = None

    # when
    tax_data = trigger_taxes_all_webhooks_sync(
        event_type,
        lambda: data,
        lines_count,
        subscribable_object=subscribable_object,
    )

    # then - first webhook skipped, second webhook called
    mock_request.assert_called_once()
    delivery = mock_request.mock_calls[0].args[0]
    assert delivery.webhook == normal_webhook
    assert tax_data == parse_tax_data(tax_data_response, lines_count)


@mock.patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
def test_trigger_tax_webhook_sync_no_defer_when_no_subscribable_object(
    mock_request,
    tax_checkout_webhook_with_defer,
    tax_data_response,
):
    # given - webhook has defer conditions but no subscribable_object passed
    tax_checkout_webhook_with_defer.subscription_query = None
    tax_checkout_webhook_with_defer.save(update_fields=["subscription_query"])

    mock_request.return_value = tax_data_response
    event_type = WebhookEventSyncType.CHECKOUT_CALCULATE_TAXES
    data = '{"key": "value"}'
    lines_count = len(tax_data_response["lines"])

    # when - subscribable_object defaults to None
    tax_data = trigger_taxes_all_webhooks_sync(
        event_type,
        lambda: data,
        lines_count,
    )

    # then - should still be called since should_defer_webhook checks object type
    mock_request.assert_called_once()
    assert tax_data == parse_tax_data(tax_data_response, lines_count)
