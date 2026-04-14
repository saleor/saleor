import json

import graphene

from ....warehouse.interface import VariantChannelStockInfo
from ...event_types import WebhookEventAsyncType
from ...transport.asynchronous.transport import create_deliveries_for_subscriptions


def test_product_variant_out_of_stock_in_channel(
    variant,
    channel_USD,
    subscription_product_variant_out_of_stock_in_channel_webhook,
):
    # given
    webhooks = [subscription_product_variant_out_of_stock_in_channel_webhook]
    event_type = WebhookEventAsyncType.PRODUCT_VARIANT_OUT_OF_STOCK_IN_CHANNEL
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    stock_info = VariantChannelStockInfo(
        variant_id=variant.id, channel_slug=channel_USD.slug
    )

    # when
    deliveries = create_deliveries_for_subscriptions(event_type, stock_info, webhooks)

    # then
    payload = json.loads(deliveries[0].payload.get_payload())
    assert payload == {
        "productVariant": {"id": variant_id},
        "channel": {"slug": channel_USD.slug},
    }
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_product_variant_back_in_stock_in_channel(
    variant,
    channel_USD,
    subscription_product_variant_back_in_stock_in_channel_webhook,
):
    # given
    webhooks = [subscription_product_variant_back_in_stock_in_channel_webhook]
    event_type = WebhookEventAsyncType.PRODUCT_VARIANT_BACK_IN_STOCK_IN_CHANNEL
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    stock_info = VariantChannelStockInfo(
        variant_id=variant.id, channel_slug=channel_USD.slug
    )

    # when
    deliveries = create_deliveries_for_subscriptions(event_type, stock_info, webhooks)

    # then
    payload = json.loads(deliveries[0].payload.get_payload())
    assert payload == {
        "productVariant": {"id": variant_id},
        "channel": {"slug": channel_USD.slug},
    }
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_product_variant_out_of_stock_for_click_and_collect(
    variant,
    channel_USD,
    subscription_product_variant_out_of_stock_for_click_and_collect_webhook,
):
    # given
    webhooks = [subscription_product_variant_out_of_stock_for_click_and_collect_webhook]
    event_type = (
        WebhookEventAsyncType.PRODUCT_VARIANT_OUT_OF_STOCK_FOR_CLICK_AND_COLLECT
    )
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    stock_info = VariantChannelStockInfo(
        variant_id=variant.id, channel_slug=channel_USD.slug
    )

    # when
    deliveries = create_deliveries_for_subscriptions(event_type, stock_info, webhooks)

    # then
    payload = json.loads(deliveries[0].payload.get_payload())
    assert payload == {
        "productVariant": {"id": variant_id},
        "channel": {"slug": channel_USD.slug},
    }
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_product_variant_back_in_stock_for_click_and_collect(
    variant,
    channel_USD,
    subscription_product_variant_back_in_stock_for_click_and_collect_webhook,
):
    # given
    webhooks = [
        subscription_product_variant_back_in_stock_for_click_and_collect_webhook
    ]
    event_type = (
        WebhookEventAsyncType.PRODUCT_VARIANT_BACK_IN_STOCK_FOR_CLICK_AND_COLLECT
    )
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    stock_info = VariantChannelStockInfo(
        variant_id=variant.id, channel_slug=channel_USD.slug
    )

    # when
    deliveries = create_deliveries_for_subscriptions(event_type, stock_info, webhooks)

    # then
    payload = json.loads(deliveries[0].payload.get_payload())
    assert payload == {
        "productVariant": {"id": variant_id},
        "channel": {"slug": channel_USD.slug},
    }
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]
