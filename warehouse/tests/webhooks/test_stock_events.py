from functools import partial
from unittest import mock

from saleor.warehouse.webhooks.stock_events import (
    trigger_product_variant_back_in_stock,
    trigger_product_variant_out_of_stock,
    trigger_product_variant_stocks_updated,
)
from saleor.webhook.event_types import WebhookEventAsyncType
from saleor.webhook.transport.asynchronous.transport import WebhookPayloadData


@mock.patch("saleor.warehouse.webhooks.stock_events.trigger_webhooks_async")
@mock.patch("saleor.warehouse.webhooks.stock_events.get_webhooks_for_event")
def test_trigger_product_variant_out_of_stock_dispatches(
    mocked_get_webhooks, mocked_trigger, any_webhook, stock, staff_user
):
    # given
    mocked_get_webhooks.return_value = [any_webhook]
    event_type = WebhookEventAsyncType.PRODUCT_VARIANT_OUT_OF_STOCK

    # when
    trigger_product_variant_out_of_stock(stock, staff_user)

    # then
    mocked_get_webhooks.assert_called_once_with(event_type)
    mocked_trigger.assert_called_once()
    args, kwargs = mocked_trigger.call_args
    assert args[0] is None
    assert args[1] == event_type
    assert args[2] == [any_webhook]
    assert kwargs["subscribable_object"] == stock
    assert kwargs["requestor"] is staff_user
    assert isinstance(kwargs["legacy_data_generator"], partial)


@mock.patch("saleor.warehouse.webhooks.stock_events.trigger_webhooks_async")
@mock.patch("saleor.warehouse.webhooks.stock_events.get_webhooks_for_event")
def test_trigger_product_variant_out_of_stock_no_webhooks_skips(
    mocked_get_webhooks, mocked_trigger, stock, staff_user
):
    # given
    mocked_get_webhooks.return_value = []

    # when
    trigger_product_variant_out_of_stock(stock, staff_user)

    # then
    mocked_trigger.assert_not_called()


@mock.patch("saleor.warehouse.webhooks.stock_events.trigger_webhooks_async")
@mock.patch("saleor.warehouse.webhooks.stock_events.get_webhooks_for_event")
def test_trigger_product_variant_out_of_stock_uses_passed_webhooks(
    mocked_get_webhooks, mocked_trigger, any_webhook, stock, staff_user
):
    # when
    trigger_product_variant_out_of_stock(stock, staff_user, webhooks=[any_webhook])

    # then
    mocked_get_webhooks.assert_not_called()
    mocked_trigger.assert_called_once()
    assert mocked_trigger.call_args.args[2] == [any_webhook]


@mock.patch("saleor.warehouse.webhooks.stock_events.trigger_webhooks_async")
@mock.patch("saleor.warehouse.webhooks.stock_events.get_webhooks_for_event")
def test_trigger_product_variant_back_in_stock_dispatches(
    mocked_get_webhooks, mocked_trigger, any_webhook, stock, app
):
    # given
    mocked_get_webhooks.return_value = [any_webhook]
    event_type = WebhookEventAsyncType.PRODUCT_VARIANT_BACK_IN_STOCK

    # when
    trigger_product_variant_back_in_stock(stock, app)

    # then
    mocked_trigger.assert_called_once()
    args, kwargs = mocked_trigger.call_args
    assert args[1] == event_type
    assert args[2] == [any_webhook]
    assert kwargs["subscribable_object"] == stock
    assert kwargs["requestor"] is app
    assert isinstance(kwargs["legacy_data_generator"], partial)


@mock.patch(
    "saleor.warehouse.webhooks.stock_events.trigger_webhooks_async_for_multiple_objects"
)
@mock.patch("saleor.warehouse.webhooks.stock_events.get_webhooks_for_event")
def test_trigger_product_variant_stocks_updated_dispatches(
    mocked_get_webhooks, mocked_trigger, any_webhook, stock, app
):
    # given
    mocked_get_webhooks.return_value = [any_webhook]
    event_type = WebhookEventAsyncType.PRODUCT_VARIANT_STOCK_UPDATED

    # when
    trigger_product_variant_stocks_updated([stock], app)

    # then
    mocked_trigger.assert_called_once()
    args, kwargs = mocked_trigger.call_args
    assert args[0] == event_type
    assert args[1] == [any_webhook]
    payloads = kwargs["webhook_payloads_data"]
    assert len(payloads) == 1
    assert isinstance(payloads[0], WebhookPayloadData)
    assert payloads[0].subscribable_object == stock
    assert isinstance(payloads[0].legacy_data_generator, partial)
    assert kwargs["requestor"] is app


@mock.patch(
    "saleor.warehouse.webhooks.stock_events.trigger_webhooks_async_for_multiple_objects"
)
@mock.patch("saleor.warehouse.webhooks.stock_events.get_webhooks_for_event")
def test_trigger_product_variant_stocks_updated_no_webhooks_skips(
    mocked_get_webhooks, mocked_trigger, stock
):
    # given
    mocked_get_webhooks.return_value = []

    # when
    trigger_product_variant_stocks_updated([stock], None)

    # then
    mocked_trigger.assert_not_called()
