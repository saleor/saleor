import json
from unittest import mock

import graphene
import pytest

from ....webhook.event_types import WebhookEventAsyncType
from ...interface import VariantChannelStockInfo
from ...webhooks.channel_stock_events import (
    _trigger,
    trigger_product_variant_back_in_stock_for_click_and_collect,
    trigger_product_variant_back_in_stock_in_channel,
    trigger_product_variant_out_of_stock_for_click_and_collect,
    trigger_product_variant_out_of_stock_in_channel,
)


@pytest.fixture
def stock_info():
    return VariantChannelStockInfo(variant_id=42, channel_slug="default")


@pytest.mark.parametrize(
    ("trigger_fn", "event_type"),
    [
        (
            trigger_product_variant_out_of_stock_in_channel,
            WebhookEventAsyncType.PRODUCT_VARIANT_OUT_OF_STOCK_IN_CHANNEL,
        ),
        (
            trigger_product_variant_back_in_stock_in_channel,
            WebhookEventAsyncType.PRODUCT_VARIANT_BACK_IN_STOCK_IN_CHANNEL,
        ),
        (
            trigger_product_variant_out_of_stock_for_click_and_collect,
            WebhookEventAsyncType.PRODUCT_VARIANT_OUT_OF_STOCK_FOR_CLICK_AND_COLLECT,
        ),
        (
            trigger_product_variant_back_in_stock_for_click_and_collect,
            WebhookEventAsyncType.PRODUCT_VARIANT_BACK_IN_STOCK_FOR_CLICK_AND_COLLECT,
        ),
    ],
)
@mock.patch("saleor.warehouse.webhooks.channel_stock_events.trigger_webhooks_async")
@mock.patch("saleor.warehouse.webhooks.channel_stock_events.get_webhooks_for_event")
def test_trigger_dispatches(
    mocked_get_webhooks,
    mocked_trigger,
    any_webhook,
    stock_info,
    site_settings,
    trigger_fn,
    event_type,
):
    # given
    site_settings.use_legacy_shipping_zone_stock_availability = False
    mocked_get_webhooks.return_value = [any_webhook]

    # when
    trigger_fn(stock_info, site_settings)

    # then
    mocked_get_webhooks.assert_called_once_with(event_type)
    mocked_trigger.assert_called_once()
    args, kwargs = mocked_trigger.call_args
    assert args[1] == event_type
    assert args[2] == [any_webhook]
    assert kwargs["subscribable_object"] is stock_info
    assert kwargs["requestor"] is None
    legacy_payload = json.loads(kwargs["legacy_data_generator"]())
    assert legacy_payload == {
        "product_variant_id": graphene.Node.to_global_id(
            "ProductVariant", stock_info.variant_id
        ),
        "channel": {"slug": stock_info.channel_slug},
    }


@mock.patch("saleor.warehouse.webhooks.channel_stock_events.trigger_webhooks_async")
@mock.patch("saleor.warehouse.webhooks.channel_stock_events.get_webhooks_for_event")
def test_trigger_skipped_when_legacy_flag_on(
    mocked_get_webhooks, mocked_trigger, stock_info, site_settings
):
    # given
    site_settings.use_legacy_shipping_zone_stock_availability = True

    # when
    _trigger(
        WebhookEventAsyncType.PRODUCT_VARIANT_OUT_OF_STOCK_IN_CHANNEL,
        stock_info,
        site_settings,
        None,
        None,
    )

    # then
    mocked_get_webhooks.assert_not_called()
    mocked_trigger.assert_not_called()


@mock.patch("saleor.warehouse.webhooks.channel_stock_events.trigger_webhooks_async")
@mock.patch("saleor.warehouse.webhooks.channel_stock_events.get_webhooks_for_event")
def test_trigger_no_webhooks_skips(
    mocked_get_webhooks, mocked_trigger, stock_info, site_settings
):
    # given
    site_settings.use_legacy_shipping_zone_stock_availability = False
    mocked_get_webhooks.return_value = []

    # when
    _trigger(
        WebhookEventAsyncType.PRODUCT_VARIANT_OUT_OF_STOCK_IN_CHANNEL,
        stock_info,
        site_settings,
        None,
        None,
    )

    # then
    mocked_trigger.assert_not_called()


@mock.patch("saleor.warehouse.webhooks.channel_stock_events.trigger_webhooks_async")
@mock.patch("saleor.warehouse.webhooks.channel_stock_events.get_webhooks_for_event")
def test_trigger_uses_passed_webhooks(
    mocked_get_webhooks,
    mocked_trigger,
    any_webhook,
    stock_info,
    site_settings,
):
    # given
    site_settings.use_legacy_shipping_zone_stock_availability = False

    # when
    _trigger(
        WebhookEventAsyncType.PRODUCT_VARIANT_OUT_OF_STOCK_IN_CHANNEL,
        stock_info,
        site_settings,
        None,
        [any_webhook],
    )

    # then
    mocked_get_webhooks.assert_not_called()
    assert mocked_trigger.call_args.args[2] == [any_webhook]


@mock.patch("saleor.warehouse.webhooks.channel_stock_events.trigger_webhooks_async")
@mock.patch("saleor.warehouse.webhooks.channel_stock_events.get_webhooks_for_event")
def test_trigger_filters_webhooks_by_channel_slug(
    mocked_get_webhooks, mocked_trigger, stock_info, site_settings
):
    # given - webhook subscription only allows a different channel
    site_settings.use_legacy_shipping_zone_stock_availability = False
    webhook = mock.Mock()
    webhook.subscription_query = "subscription { event { ... } }"
    webhook.filterable_channel_slugs = ["other-channel"]
    mocked_get_webhooks.return_value = [webhook]

    # when
    _trigger(
        WebhookEventAsyncType.PRODUCT_VARIANT_OUT_OF_STOCK_IN_CHANNEL,
        stock_info,
        site_settings,
        None,
        None,
    )

    # then
    mocked_trigger.assert_not_called()


@mock.patch("saleor.warehouse.webhooks.channel_stock_events.trigger_webhooks_async")
@mock.patch("saleor.warehouse.webhooks.channel_stock_events.get_webhooks_for_event")
def test_trigger_passes_through_when_subscription_has_no_channel_filter(
    mocked_get_webhooks, mocked_trigger, stock_info, site_settings
):
    # given
    site_settings.use_legacy_shipping_zone_stock_availability = False
    webhook = mock.Mock()
    webhook.subscription_query = "subscription { event { ... } }"
    webhook.filterable_channel_slugs = []
    mocked_get_webhooks.return_value = [webhook]

    # when
    _trigger(
        WebhookEventAsyncType.PRODUCT_VARIANT_OUT_OF_STOCK_IN_CHANNEL,
        stock_info,
        site_settings,
        None,
        None,
    )

    # then
    mocked_trigger.assert_called_once()
    assert mocked_trigger.call_args.args[2] == [webhook]
