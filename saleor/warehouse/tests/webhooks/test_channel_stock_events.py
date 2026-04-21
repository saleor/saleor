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

TRIGGER_PATH = (
    "saleor.warehouse.webhooks.channel_stock_events"
    ".trigger_webhooks_async_for_multiple_objects"
)
GET_WEBHOOKS_PATH = (
    "saleor.warehouse.webhooks.channel_stock_events.get_webhooks_for_event"
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
@mock.patch(TRIGGER_PATH)
@mock.patch(GET_WEBHOOKS_PATH)
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
    trigger_fn([stock_info], site_settings)

    # then
    mocked_get_webhooks.assert_called_once_with(event_type)
    mocked_trigger.assert_called_once()
    kwargs = mocked_trigger.call_args.kwargs
    assert kwargs["event_type"] == event_type
    assert kwargs["webhooks"] == [any_webhook]
    assert kwargs["requestor"] is None
    payloads = kwargs["webhook_payloads_data"]
    assert len(payloads) == 1
    assert payloads[0].subscribable_object is stock_info
    legacy_payload = json.loads(payloads[0].legacy_data_generator())
    assert legacy_payload == {
        "product_variant_id": graphene.Node.to_global_id(
            "ProductVariant", stock_info.variant_id
        ),
        "channel": {"slug": stock_info.channel_slug},
    }


@mock.patch(TRIGGER_PATH)
@mock.patch(GET_WEBHOOKS_PATH)
def test_trigger_skipped_when_legacy_flag_on(
    mocked_get_webhooks, mocked_trigger, stock_info, site_settings
):
    # given
    site_settings.use_legacy_shipping_zone_stock_availability = True

    # when
    _trigger(
        WebhookEventAsyncType.PRODUCT_VARIANT_OUT_OF_STOCK_IN_CHANNEL,
        [stock_info],
        site_settings,
        None,
        None,
    )

    # then
    mocked_get_webhooks.assert_not_called()
    mocked_trigger.assert_not_called()


@mock.patch(TRIGGER_PATH)
@mock.patch(GET_WEBHOOKS_PATH)
def test_trigger_empty_stock_infos_skips(
    mocked_get_webhooks, mocked_trigger, site_settings
):
    # given
    site_settings.use_legacy_shipping_zone_stock_availability = False

    # when
    _trigger(
        WebhookEventAsyncType.PRODUCT_VARIANT_OUT_OF_STOCK_IN_CHANNEL,
        [],
        site_settings,
        None,
        None,
    )

    # then
    mocked_get_webhooks.assert_not_called()
    mocked_trigger.assert_not_called()


@mock.patch(TRIGGER_PATH)
@mock.patch(GET_WEBHOOKS_PATH)
def test_trigger_no_webhooks_skips(
    mocked_get_webhooks, mocked_trigger, stock_info, site_settings
):
    # given
    site_settings.use_legacy_shipping_zone_stock_availability = False
    mocked_get_webhooks.return_value = []

    # when
    _trigger(
        WebhookEventAsyncType.PRODUCT_VARIANT_OUT_OF_STOCK_IN_CHANNEL,
        [stock_info],
        site_settings,
        None,
        None,
    )

    # then
    mocked_trigger.assert_not_called()


@mock.patch(TRIGGER_PATH)
@mock.patch(GET_WEBHOOKS_PATH)
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
        [stock_info],
        site_settings,
        None,
        [any_webhook],
    )

    # then
    mocked_get_webhooks.assert_not_called()
    assert mocked_trigger.call_args.kwargs["webhooks"] == [any_webhook]


@mock.patch(TRIGGER_PATH)
@mock.patch(GET_WEBHOOKS_PATH)
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
        [stock_info],
        site_settings,
        None,
        None,
    )

    # then
    mocked_trigger.assert_not_called()


@mock.patch(TRIGGER_PATH)
@mock.patch(GET_WEBHOOKS_PATH)
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
        [stock_info],
        site_settings,
        None,
        None,
    )

    # then
    mocked_trigger.assert_called_once()
    assert mocked_trigger.call_args.kwargs["webhooks"] == [webhook]


@mock.patch(TRIGGER_PATH)
@mock.patch(GET_WEBHOOKS_PATH)
def test_trigger_groups_multiple_channels_into_separate_calls(
    mocked_get_webhooks, mocked_trigger, any_webhook, site_settings
):
    # given - two stock infos in different channels, one shared subscription webhook
    site_settings.use_legacy_shipping_zone_stock_availability = False
    mocked_get_webhooks.return_value = [any_webhook]
    info_a = VariantChannelStockInfo(variant_id=1, channel_slug="default")
    info_b = VariantChannelStockInfo(variant_id=2, channel_slug="other")

    # when
    _trigger(
        WebhookEventAsyncType.PRODUCT_VARIANT_OUT_OF_STOCK_IN_CHANNEL,
        [info_a, info_b],
        site_settings,
        None,
        None,
    )

    # then - one call per channel, each with a single payload
    assert mocked_trigger.call_count == 2
    dispatched = {
        call.kwargs["webhook_payloads_data"][0].subscribable_object.channel_slug: [
            payload.subscribable_object.variant_id
            for payload in call.kwargs["webhook_payloads_data"]
        ]
        for call in mocked_trigger.call_args_list
    }
    assert dispatched == {"default": [info_a.variant_id], "other": [info_b.variant_id]}


@mock.patch(TRIGGER_PATH)
@mock.patch(GET_WEBHOOKS_PATH)
def test_trigger_batches_multiple_variants_in_same_channel(
    mocked_get_webhooks, mocked_trigger, any_webhook, site_settings
):
    # given - two variants in the same channel
    site_settings.use_legacy_shipping_zone_stock_availability = False
    mocked_get_webhooks.return_value = [any_webhook]
    info_a = VariantChannelStockInfo(variant_id=1, channel_slug="default")
    info_b = VariantChannelStockInfo(variant_id=2, channel_slug="default")

    # when
    _trigger(
        WebhookEventAsyncType.PRODUCT_VARIANT_OUT_OF_STOCK_IN_CHANNEL,
        [info_a, info_b],
        site_settings,
        None,
        None,
    )

    # then - one call carrying both payloads
    mocked_trigger.assert_called_once()
    payloads = mocked_trigger.call_args.kwargs["webhook_payloads_data"]
    assert [payload.subscribable_object for payload in payloads] == [info_a, info_b]
