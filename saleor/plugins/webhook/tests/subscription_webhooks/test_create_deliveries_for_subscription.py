import json
from unittest.mock import patch

import graphene
import pytest

from .....channel.models import Channel
from .....giftcard.models import GiftCard
from .....graphql.webhook.subscription_payload import validate_subscription_query
from .....menu.models import Menu, MenuItem
from .....product.models import Category
from .....shipping.models import ShippingMethod, ShippingZone
from .....webhook.event_types import WebhookEventAsyncType
from ...tasks import create_deliveries_for_subscriptions, logger
from . import subscription_queries
from .payloads import (
    generate_category_payload,
    generate_collection_payload,
    generate_customer_payload,
    generate_fulfillment_payload,
    generate_gift_card_payload,
    generate_invoice_payload,
    generate_menu_item_payload,
    generate_menu_payload,
    generate_page_payload,
    generate_sale_payload,
    generate_shipping_method_payload,
    generate_voucher_payload,
    generate_warehouse_payload,
)


def generate_expected_payload_for_app(app, app_global_id):
    return json.dumps(
        {
            "app": {
                "id": app_global_id,
                "isActive": app.is_active,
                "name": app.name,
                "appUrl": app.app_url,
            },
            "meta": None,
        }
    )


def test_app_installed(app, subscription_app_installed_webhook):
    # given
    webhooks = [subscription_app_installed_webhook]
    event_type = WebhookEventAsyncType.APP_INSTALLED
    app_id = graphene.Node.to_global_id("App", app.id)

    # when
    deliveries = create_deliveries_for_subscriptions(event_type, app, webhooks)

    # then
    expected_payload = generate_expected_payload_for_app(app, app_id)
    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_app_updated(app, subscription_app_updated_webhook):
    # given
    webhooks = [subscription_app_updated_webhook]
    event_type = WebhookEventAsyncType.APP_UPDATED
    gift_card_id = graphene.Node.to_global_id("App", app.id)

    # when
    deliveries = create_deliveries_for_subscriptions(event_type, app, webhooks)

    # then
    expected_payload = generate_expected_payload_for_app(app, gift_card_id)
    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_app_deleted(app, subscription_app_deleted_webhook):
    # given
    webhooks = [subscription_app_deleted_webhook]

    id = app.id
    app.delete()
    app.id = id

    event_type = WebhookEventAsyncType.APP_DELETED
    app_id = graphene.Node.to_global_id("App", app.id)

    # when
    deliveries = create_deliveries_for_subscriptions(event_type, app, webhooks)

    # then
    expected_payload = generate_expected_payload_for_app(app, app_id)
    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


@pytest.mark.parametrize("status", [True, False])
def test_app_status_changed(status, app, subscription_app_status_changed_webhook):
    # given
    webhooks = [subscription_app_status_changed_webhook]

    app.is_active = status
    app.save(update_fields=["is_active"])

    event_type = WebhookEventAsyncType.APP_STATUS_CHANGED
    app_id = graphene.Node.to_global_id("App", app.id)

    # when
    deliveries = create_deliveries_for_subscriptions(event_type, app, webhooks)

    # then
    expected_payload = generate_expected_payload_for_app(app, app_id)
    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_category_created(
    categories_tree_with_published_products,
    subscription_category_created_webhook,
):
    # given
    parent_category = categories_tree_with_published_products
    webhooks = [subscription_category_created_webhook]
    event_type = WebhookEventAsyncType.CATEGORY_CREATED
    expected_payload = generate_category_payload(parent_category)

    # when
    deliveries = create_deliveries_for_subscriptions(
        event_type, parent_category, webhooks
    )

    # then
    assert deliveries[0].payload.payload == json.dumps(expected_payload)
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_category_updated(
    categories_tree_with_published_products,
    subscription_category_updated_webhook,
    channel_USD,
):
    # given
    parent_category = categories_tree_with_published_products
    webhooks = [subscription_category_updated_webhook]
    event_type = WebhookEventAsyncType.CATEGORY_UPDATED
    expected_payload = generate_category_payload(parent_category)

    # when
    deliveries = create_deliveries_for_subscriptions(
        event_type, parent_category, webhooks
    )

    # then
    assert deliveries[0].payload.payload == json.dumps(expected_payload)
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_category_deleted(category, subscription_category_deleted_webhook):
    # given
    webhooks = [subscription_category_deleted_webhook]

    category_query = Category.objects.filter(pk=category.id)
    category_instances = [cat for cat in category_query]
    category_query.delete()

    event_type = WebhookEventAsyncType.CATEGORY_DELETED
    category_id = graphene.Node.to_global_id("Category", category_instances[0].id)

    # when
    deliveries = create_deliveries_for_subscriptions(
        event_type, category_instances[0], webhooks
    )

    # then
    expected_payload = json.dumps({"category": {"id": category_id}, "meta": None})
    assert category_instances[0].id is not None
    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_channel_created(channel_USD, subscription_channel_created_webhook):
    # given
    webhooks = [subscription_channel_created_webhook]
    event_type = WebhookEventAsyncType.CHANNEL_CREATED
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)

    # when
    deliveries = create_deliveries_for_subscriptions(event_type, channel_USD, webhooks)

    # then
    expected_payload = json.dumps({"channel": {"id": channel_id}, "meta": None})
    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_channel_updated(channel_USD, subscription_channel_updated_webhook):
    # given
    webhooks = [subscription_channel_updated_webhook]
    event_type = WebhookEventAsyncType.CHANNEL_UPDATED
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)

    # when
    deliveries = create_deliveries_for_subscriptions(event_type, channel_USD, webhooks)

    # then
    expected_payload = json.dumps({"channel": {"id": channel_id}, "meta": None})
    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_channel_deleted(channel_USD, subscription_channel_deleted_webhook):
    # given
    webhooks = [subscription_channel_deleted_webhook]

    channel_query = Channel.objects.filter(pk=channel_USD.id)
    channel_instances = [channel for channel in channel_query]
    channel_query.delete()

    event_type = WebhookEventAsyncType.CHANNEL_DELETED
    channel_id = graphene.Node.to_global_id("Channel", channel_instances[0].id)

    # when
    deliveries = create_deliveries_for_subscriptions(
        event_type, channel_instances[0], webhooks
    )

    # then
    expected_payload = json.dumps({"channel": {"id": channel_id}, "meta": None})
    assert channel_instances[0].id is not None
    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


@pytest.mark.parametrize("status", [True, False])
def test_channel_status_changed(
    status, channel_USD, subscription_channel_status_changed_webhook
):
    # given
    webhooks = [subscription_channel_status_changed_webhook]

    channel_USD.is_active = status
    channel_USD.save(update_fields=["is_active"])

    event_type = WebhookEventAsyncType.CHANNEL_STATUS_CHANGED
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)

    # when
    deliveries = create_deliveries_for_subscriptions(event_type, channel_USD, webhooks)

    # then
    expected_payload = json.dumps(
        {"channel": {"id": channel_id, "isActive": status}, "meta": None}
    )
    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_gift_card_created(gift_card, subscription_gift_card_created_webhook):
    # given
    webhooks = [subscription_gift_card_created_webhook]
    event_type = WebhookEventAsyncType.GIFT_CARD_CREATED
    gift_card_id = graphene.Node.to_global_id("GiftCard", gift_card.id)

    # when
    deliveries = create_deliveries_for_subscriptions(event_type, gift_card, webhooks)

    # then
    expected_payload = generate_gift_card_payload(gift_card, gift_card_id)
    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_gift_card_updated(gift_card, subscription_gift_card_updated_webhook):
    # given
    webhooks = [subscription_gift_card_updated_webhook]
    event_type = WebhookEventAsyncType.GIFT_CARD_UPDATED
    gift_card_id = graphene.Node.to_global_id("GiftCard", gift_card.id)

    # when
    deliveries = create_deliveries_for_subscriptions(event_type, gift_card, webhooks)

    # then
    expected_payload = generate_gift_card_payload(gift_card, gift_card_id)
    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_gift_card_deleted(gift_card, subscription_gift_card_deleted_webhook):
    # given
    webhooks = [subscription_gift_card_deleted_webhook]

    gift_card_query = GiftCard.objects.filter(pk=gift_card.id)
    gift_card_instances = [card for card in gift_card_query]
    gift_card_query.delete()

    event_type = WebhookEventAsyncType.GIFT_CARD_DELETED
    gift_card_id = graphene.Node.to_global_id("GiftCard", gift_card_instances[0].id)

    # when
    deliveries = create_deliveries_for_subscriptions(
        event_type, gift_card_instances[0], webhooks
    )

    # then
    expected_payload = generate_gift_card_payload(gift_card, gift_card_id)
    assert gift_card_instances[0].id is not None
    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


@pytest.mark.parametrize("status", [True, False])
def test_gift_card_status_changed(
    status, gift_card, subscription_gift_card_status_changed_webhook
):
    # given
    webhooks = [subscription_gift_card_status_changed_webhook]

    gift_card.is_active = status
    gift_card.save(update_fields=["is_active"])

    event_type = WebhookEventAsyncType.GIFT_CARD_STATUS_CHANGED
    gift_card_id = graphene.Node.to_global_id("GiftCard", gift_card.id)

    # when
    deliveries = create_deliveries_for_subscriptions(event_type, gift_card, webhooks)

    # then
    expected_payload = generate_gift_card_payload(gift_card, gift_card_id)
    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_menu_created(menu, subscription_menu_created_webhook):
    # given
    webhooks = [subscription_menu_created_webhook]
    event_type = WebhookEventAsyncType.MENU_CREATED
    menu_id = graphene.Node.to_global_id("Menu", menu.id)

    # when
    deliveries = create_deliveries_for_subscriptions(event_type, menu, webhooks)

    # then
    expected_payload = json.dumps(generate_menu_payload(menu, menu_id))
    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_menu_updated(menu, subscription_menu_updated_webhook):
    # given
    webhooks = [subscription_menu_updated_webhook]
    event_type = WebhookEventAsyncType.MENU_UPDATED
    menu_id = graphene.Node.to_global_id("Menu", menu.id)

    # when
    deliveries = create_deliveries_for_subscriptions(event_type, menu, webhooks)

    # then
    expected_payload = json.dumps(generate_menu_payload(menu, menu_id))
    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_menu_deleted(menu, subscription_menu_deleted_webhook):
    # given
    webhooks = [subscription_menu_deleted_webhook]

    menu_query = Menu.objects.filter(pk=menu.id)
    menu_instances = [menu for menu in menu_query]
    menu_query.delete()

    event_type = WebhookEventAsyncType.MENU_DELETED
    menu_id = graphene.Node.to_global_id("Menu", menu_instances[0].id)

    # when
    deliveries = create_deliveries_for_subscriptions(
        event_type, menu_instances[0], webhooks
    )

    # then
    expected_payload = json.dumps(generate_menu_payload(menu, menu_id))
    assert menu_instances[0].id is not None
    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_menu_item_created(menu_item, subscription_menu_item_created_webhook):
    # given
    webhooks = [subscription_menu_item_created_webhook]
    event_type = WebhookEventAsyncType.MENU_ITEM_CREATED
    menu_item_id = graphene.Node.to_global_id("MenuItem", menu_item.id)

    # when
    deliveries = create_deliveries_for_subscriptions(event_type, menu_item, webhooks)

    # then
    expected_payload = json.dumps(generate_menu_item_payload(menu_item, menu_item_id))
    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_menu_item_updated(menu_item, subscription_menu_item_updated_webhook):
    # given
    webhooks = [subscription_menu_item_updated_webhook]
    event_type = WebhookEventAsyncType.MENU_ITEM_UPDATED
    menu_item_id = graphene.Node.to_global_id("MenuItem", menu_item.id)

    # when
    deliveries = create_deliveries_for_subscriptions(event_type, menu_item, webhooks)

    # then
    expected_payload = json.dumps(generate_menu_item_payload(menu_item, menu_item_id))
    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_menu_item_deleted(menu_item, subscription_menu_item_deleted_webhook):
    # given
    webhooks = [subscription_menu_item_deleted_webhook]

    menu_item_query = MenuItem.objects.filter(pk=menu_item.id)
    menu_item_instances = [menu for menu in menu_item_query]
    menu_item_query.delete()

    event_type = WebhookEventAsyncType.MENU_ITEM_DELETED
    menu_item_id = graphene.Node.to_global_id("MenuItem", menu_item_instances[0].id)

    # when
    deliveries = create_deliveries_for_subscriptions(
        event_type, menu_item_instances[0], webhooks
    )

    # then
    expected_payload = json.dumps(
        generate_menu_item_payload(menu_item_instances[0], menu_item_id)
    )
    assert menu_item_instances[0].id is not None
    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_shipping_price_created(
    shipping_method, subscription_shipping_price_created_webhook
):
    # given
    webhooks = [subscription_shipping_price_created_webhook]
    event_type = WebhookEventAsyncType.SHIPPING_PRICE_CREATED
    expected_payload = generate_shipping_method_payload(shipping_method)

    # when
    deliveries = create_deliveries_for_subscriptions(
        event_type, shipping_method, webhooks
    )

    # then
    assert deliveries[0].payload.payload == json.dumps(expected_payload)
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_shipping_price_updated(
    shipping_method, subscription_shipping_price_updated_webhook
):
    # given
    webhooks = [subscription_shipping_price_updated_webhook]
    event_type = WebhookEventAsyncType.SHIPPING_PRICE_UPDATED
    expected_payload = generate_shipping_method_payload(shipping_method)

    # when
    deliveries = create_deliveries_for_subscriptions(
        event_type, shipping_method, webhooks
    )

    # then
    assert deliveries[0].payload.payload == json.dumps(expected_payload)
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_shipping_price_deleted(
    shipping_method, subscription_shipping_price_deleted_webhook
):
    # given
    webhooks = [subscription_shipping_price_deleted_webhook]
    event_type = WebhookEventAsyncType.SHIPPING_PRICE_DELETED

    shipping_methods_query = ShippingMethod.objects.filter(pk=shipping_method.id)
    method_instances = [method for method in shipping_methods_query]
    shipping_methods_query.delete()

    shipping_method_id = graphene.Node.to_global_id(
        "ShippingMethodType", method_instances[0].id
    )

    # when
    deliveries = create_deliveries_for_subscriptions(
        event_type, method_instances[0], webhooks
    )

    # then
    expected_payload = json.dumps(
        {
            "shippingMethod": {"id": shipping_method_id, "name": shipping_method.name},
            "meta": None,
        }
    )
    assert method_instances[0].id is not None
    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_shipping_zone_created(
    shipping_zone, subscription_shipping_zone_created_webhook
):
    # given
    webhooks = [subscription_shipping_zone_created_webhook]
    event_type = WebhookEventAsyncType.SHIPPING_ZONE_CREATED
    shipping_zone_id = graphene.Node.to_global_id("ShippingZone", shipping_zone.id)

    # when
    deliveries = create_deliveries_for_subscriptions(
        event_type, shipping_zone, webhooks
    )

    # then
    expected_payload = json.dumps(
        {
            "shippingZone": {
                "id": shipping_zone_id,
                "name": shipping_zone.name,
                "countries": [{"code": c.code} for c in shipping_zone.countries],
                "channels": [{"name": c.name} for c in shipping_zone.channels.all()],
            },
            "meta": None,
        }
    )

    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_shipping_zone_updated(
    shipping_zone, subscription_shipping_zone_updated_webhook
):
    # given
    webhooks = [subscription_shipping_zone_updated_webhook]
    event_type = WebhookEventAsyncType.SHIPPING_ZONE_UPDATED
    shipping_zone_id = graphene.Node.to_global_id("ShippingZone", shipping_zone.id)

    # when
    deliveries = create_deliveries_for_subscriptions(
        event_type, shipping_zone, webhooks
    )

    # then
    expected_payload = json.dumps(
        {
            "shippingZone": {
                "id": shipping_zone_id,
                "name": shipping_zone.name,
                "countries": [{"code": c.code} for c in shipping_zone.countries],
                "channels": [{"name": c.name} for c in shipping_zone.channels.all()],
            },
            "meta": None,
        }
    )
    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_shipping_zone_deleted(
    shipping_zone, subscription_shipping_zone_deleted_webhook
):
    # given
    webhooks = [subscription_shipping_zone_deleted_webhook]
    event_type = WebhookEventAsyncType.SHIPPING_ZONE_DELETED

    shipping_zones_query = ShippingZone.objects.filter(pk=shipping_zone.id)
    zones_instances = [zone for zone in shipping_zones_query]
    shipping_zones_query.delete()

    shipping_zone_id = graphene.Node.to_global_id("ShippingZone", zones_instances[0].id)

    # when
    deliveries = create_deliveries_for_subscriptions(
        event_type, zones_instances[0], webhooks
    )

    # then
    expected_payload = json.dumps(
        {
            "shippingZone": {"id": shipping_zone_id, "name": shipping_zone.name},
            "meta": None,
        }
    )
    assert zones_instances[0].id is not None
    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_product_created(product, subscription_product_created_webhook):
    webhooks = [subscription_product_created_webhook]
    event_type = WebhookEventAsyncType.PRODUCT_CREATED
    product_id = graphene.Node.to_global_id("Product", product.id)
    deliveries = create_deliveries_for_subscriptions(event_type, product, webhooks)
    expected_payload = json.dumps({"product": {"id": product_id}, "meta": None})

    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_product_updated(product, subscription_product_updated_webhook):
    webhooks = [subscription_product_updated_webhook]
    event_type = WebhookEventAsyncType.PRODUCT_UPDATED
    product_id = graphene.Node.to_global_id("Product", product.id)
    deliveries = create_deliveries_for_subscriptions(event_type, product, webhooks)
    expected_payload = json.dumps({"product": {"id": product_id}, "meta": None})

    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_product_deleted(product, subscription_product_deleted_webhook):
    webhooks = [subscription_product_deleted_webhook]
    event_type = WebhookEventAsyncType.PRODUCT_DELETED
    product_id = graphene.Node.to_global_id("Product", product.id)
    deliveries = create_deliveries_for_subscriptions(event_type, product, webhooks)
    expected_payload = json.dumps({"product": {"id": product_id}, "meta": None})

    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_product_variant_created(variant, subscription_product_variant_created_webhook):
    webhooks = [subscription_product_variant_created_webhook]
    event_type = WebhookEventAsyncType.PRODUCT_VARIANT_CREATED
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    deliveries = create_deliveries_for_subscriptions(event_type, variant, webhooks)
    expected_payload = json.dumps({"productVariant": {"id": variant_id}, "meta": None})

    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_product_variant_updated(variant, subscription_product_variant_updated_webhook):
    webhooks = [subscription_product_variant_updated_webhook]
    event_type = WebhookEventAsyncType.PRODUCT_VARIANT_UPDATED
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    deliveries = create_deliveries_for_subscriptions(event_type, variant, webhooks)
    expected_payload = json.dumps({"productVariant": {"id": variant_id}, "meta": None})

    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_product_variant_deleted(variant, subscription_product_variant_deleted_webhook):
    webhooks = [subscription_product_variant_deleted_webhook]
    event_type = WebhookEventAsyncType.PRODUCT_VARIANT_DELETED
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    deliveries = create_deliveries_for_subscriptions(event_type, variant, webhooks)
    expected_payload = json.dumps({"productVariant": {"id": variant_id}, "meta": None})

    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_product_variant_out_of_stock(
    stock, subscription_product_variant_out_of_stock_webhook
):
    webhooks = [subscription_product_variant_out_of_stock_webhook]
    event_type = WebhookEventAsyncType.PRODUCT_VARIANT_OUT_OF_STOCK
    variant_id = graphene.Node.to_global_id("ProductVariant", stock.product_variant.id)
    deliveries = create_deliveries_for_subscriptions(event_type, stock, webhooks)
    expected_payload = json.dumps({"productVariant": {"id": variant_id}, "meta": None})

    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_product_variant_back_in_stock(
    stock, subscription_product_variant_back_in_stock_webhook
):
    webhooks = [subscription_product_variant_back_in_stock_webhook]
    event_type = WebhookEventAsyncType.PRODUCT_VARIANT_BACK_IN_STOCK
    variant_id = graphene.Node.to_global_id("ProductVariant", stock.product_variant.id)
    deliveries = create_deliveries_for_subscriptions(event_type, stock, webhooks)
    expected_payload = json.dumps({"productVariant": {"id": variant_id}, "meta": None})

    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_order_created(order, subscription_order_created_webhook):
    webhooks = [subscription_order_created_webhook]
    event_type = WebhookEventAsyncType.ORDER_CREATED
    order_id = graphene.Node.to_global_id("Order", order.id)
    deliveries = create_deliveries_for_subscriptions(event_type, order, webhooks)
    expected_payload = json.dumps({"order": {"id": order_id}, "meta": None})

    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_order_confirmed(order, subscription_order_confirmed_webhook):
    webhooks = [subscription_order_confirmed_webhook]
    event_type = WebhookEventAsyncType.ORDER_CONFIRMED
    order_id = graphene.Node.to_global_id("Order", order.id)
    deliveries = create_deliveries_for_subscriptions(event_type, order, webhooks)
    expected_payload = json.dumps({"order": {"id": order_id}, "meta": None})

    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_order_fully_paid(order, subscription_order_fully_paid_webhook):
    webhooks = [subscription_order_fully_paid_webhook]
    event_type = WebhookEventAsyncType.ORDER_FULLY_PAID
    order_id = graphene.Node.to_global_id("Order", order.id)
    deliveries = create_deliveries_for_subscriptions(event_type, order, webhooks)
    expected_payload = json.dumps({"order": {"id": order_id}, "meta": None})

    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_order_updated(order, subscription_order_updated_webhook):
    webhooks = [subscription_order_updated_webhook]
    event_type = WebhookEventAsyncType.ORDER_UPDATED
    order_id = graphene.Node.to_global_id("Order", order.id)
    deliveries = create_deliveries_for_subscriptions(event_type, order, webhooks)
    expected_payload = json.dumps({"order": {"id": order_id}, "meta": None})

    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_order_cancelled(order, subscription_order_cancelled_webhook):
    webhooks = [subscription_order_cancelled_webhook]
    event_type = WebhookEventAsyncType.ORDER_CANCELLED
    order_id = graphene.Node.to_global_id("Order", order.id)
    deliveries = create_deliveries_for_subscriptions(event_type, order, webhooks)
    expected_payload = json.dumps({"order": {"id": order_id}, "meta": None})

    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_order_fulfilled(order, subscription_order_fulfilled_webhook):
    webhooks = [subscription_order_fulfilled_webhook]
    event_type = WebhookEventAsyncType.ORDER_FULFILLED
    order_id = graphene.Node.to_global_id("Order", order.id)
    deliveries = create_deliveries_for_subscriptions(event_type, order, webhooks)
    expected_payload = json.dumps({"order": {"id": order_id}, "meta": None})

    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_draft_order_created(order, subscription_draft_order_created_webhook):
    webhooks = [subscription_draft_order_created_webhook]
    event_type = WebhookEventAsyncType.DRAFT_ORDER_CREATED
    order_id = graphene.Node.to_global_id("Order", order.id)
    deliveries = create_deliveries_for_subscriptions(event_type, order, webhooks)
    expected_payload = json.dumps({"order": {"id": order_id}, "meta": None})

    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_draft_order_updated(order, subscription_draft_order_updated_webhook):
    webhooks = [subscription_draft_order_updated_webhook]
    event_type = WebhookEventAsyncType.DRAFT_ORDER_UPDATED
    order_id = graphene.Node.to_global_id("Order", order.id)
    deliveries = create_deliveries_for_subscriptions(event_type, order, webhooks)
    expected_payload = json.dumps({"order": {"id": order_id}, "meta": None})

    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_draft_order_deleted(order, subscription_draft_order_deleted_webhook):
    webhooks = [subscription_draft_order_deleted_webhook]
    event_type = WebhookEventAsyncType.DRAFT_ORDER_DELETED
    order_id = graphene.Node.to_global_id("Order", order.id)
    deliveries = create_deliveries_for_subscriptions(event_type, order, webhooks)
    expected_payload = json.dumps({"order": {"id": order_id}, "meta": None})

    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_sale_created(sale, subscription_sale_created_webhook):
    # given
    webhooks = [subscription_sale_created_webhook]
    event_type = WebhookEventAsyncType.SALE_CREATED
    expected_payload = generate_sale_payload(sale)

    # when
    deliveries = create_deliveries_for_subscriptions(event_type, sale, webhooks)

    # then
    assert deliveries[0].payload.payload == json.dumps(expected_payload)
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_sale_updated(sale, subscription_sale_updated_webhook):
    # given
    webhooks = [subscription_sale_updated_webhook]
    event_type = WebhookEventAsyncType.SALE_UPDATED
    expected_payload = generate_sale_payload(sale)

    # when
    deliveries = create_deliveries_for_subscriptions(event_type, sale, webhooks)

    # hen
    assert deliveries[0].payload.payload == json.dumps(expected_payload)
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_sale_deleted(sale, subscription_sale_deleted_webhook):
    # given
    webhooks = [subscription_sale_deleted_webhook]
    event_type = WebhookEventAsyncType.SALE_DELETED
    expected_payload = generate_sale_payload(sale)

    # when
    deliveries = create_deliveries_for_subscriptions(event_type, sale, webhooks)

    # then
    assert deliveries[0].payload.payload == json.dumps(expected_payload)
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_invoice_requested(fulfilled_order, subscription_invoice_requested_webhook):
    # given
    webhooks = [subscription_invoice_requested_webhook]
    event_type = WebhookEventAsyncType.INVOICE_REQUESTED
    invoice = fulfilled_order.invoices.first()
    expected_payload = generate_invoice_payload(invoice)

    # when
    deliveries = create_deliveries_for_subscriptions(event_type, invoice, webhooks)

    # then
    assert deliveries[0].payload.payload == json.dumps(expected_payload)
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_invoice_deleted(fulfilled_order, subscription_invoice_deleted_webhook):
    # given
    webhooks = [subscription_invoice_deleted_webhook]
    event_type = WebhookEventAsyncType.INVOICE_DELETED
    invoice = fulfilled_order.invoices.first()
    expected_payload = generate_invoice_payload(invoice)

    # when
    deliveries = create_deliveries_for_subscriptions(event_type, invoice, webhooks)

    # then
    assert deliveries[0].payload.payload == json.dumps(expected_payload)
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_invoice_sent(fulfilled_order, subscription_invoice_sent_webhook):
    # given
    webhooks = [subscription_invoice_sent_webhook]
    event_type = WebhookEventAsyncType.INVOICE_SENT
    invoice = fulfilled_order.invoices.first()
    expected_payload = generate_invoice_payload(invoice)

    # when
    deliveries = create_deliveries_for_subscriptions(event_type, invoice, webhooks)

    # then
    assert deliveries[0].payload.payload == json.dumps(expected_payload)
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_fulfillment_created(fulfillment, subscription_fulfillment_created_webhook):
    # given
    webhooks = [subscription_fulfillment_created_webhook]
    event_type = WebhookEventAsyncType.FULFILLMENT_CREATED
    expected_payload = generate_fulfillment_payload(fulfillment)

    # when
    deliveries = create_deliveries_for_subscriptions(event_type, fulfillment, webhooks)

    # then
    assert deliveries[0].payload.payload == json.dumps(expected_payload)
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_fulfillment_canceled(fulfillment, subscription_fulfillment_canceled_webhook):
    # given
    webhooks = [subscription_fulfillment_canceled_webhook]
    event_type = WebhookEventAsyncType.FULFILLMENT_CANCELED
    expected_payload = generate_fulfillment_payload(fulfillment)

    # when
    deliveries = create_deliveries_for_subscriptions(event_type, fulfillment, webhooks)

    # then
    assert deliveries[0].payload.payload == json.dumps(expected_payload)
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_customer_created(customer_user, subscription_customer_created_webhook):
    # given
    webhooks = [subscription_customer_created_webhook]
    event_type = WebhookEventAsyncType.CUSTOMER_CREATED
    expected_payload = json.dumps(generate_customer_payload(customer_user))

    # when
    deliveries = create_deliveries_for_subscriptions(
        event_type, customer_user, webhooks
    )

    # then
    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_customer_updated(customer_user, subscription_customer_updated_webhook):
    # given
    webhooks = [subscription_customer_updated_webhook]
    event_type = WebhookEventAsyncType.CUSTOMER_UPDATED
    expected_payload = json.dumps(generate_customer_payload(customer_user))

    # when
    deliveries = create_deliveries_for_subscriptions(
        event_type, customer_user, webhooks
    )

    # then
    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_collection_created(
    collection_with_products, subscription_collection_created_webhook
):
    # given
    collection = collection_with_products[0].collections.first()
    webhooks = [subscription_collection_created_webhook]
    event_type = WebhookEventAsyncType.COLLECTION_CREATED
    expected_payload = generate_collection_payload(collection)

    # when
    deliveries = create_deliveries_for_subscriptions(event_type, collection, webhooks)

    # then
    assert deliveries[0].payload.payload == json.dumps(expected_payload)
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_collection_updated(
    collection_with_products, subscription_collection_updated_webhook
):
    # given
    webhooks = [subscription_collection_updated_webhook]
    collection = collection_with_products[0].collections.first()
    event_type = WebhookEventAsyncType.COLLECTION_UPDATED
    expected_payload = generate_collection_payload(collection)

    # when
    deliveries = create_deliveries_for_subscriptions(event_type, collection, webhooks)

    # then
    assert deliveries[0].payload.payload == json.dumps(expected_payload)
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_collection_deleted(
    collection_with_products, subscription_collection_deleted_webhook
):
    # given
    webhooks = [subscription_collection_deleted_webhook]
    collection = collection_with_products[0].collections.first()
    event_type = WebhookEventAsyncType.COLLECTION_DELETED
    expected_payload = generate_collection_payload(collection)

    # when
    deliveries = create_deliveries_for_subscriptions(event_type, collection, webhooks)

    # then
    assert deliveries[0].payload.payload == json.dumps(expected_payload)
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_checkout_create(checkout, subscription_checkout_created_webhook):
    webhooks = [subscription_checkout_created_webhook]
    event_type = WebhookEventAsyncType.CHECKOUT_CREATED
    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)
    deliveries = create_deliveries_for_subscriptions(event_type, checkout, webhooks)
    expected_payload = json.dumps({"checkout": {"id": checkout_id}, "meta": None})
    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_checkout_update(checkout, subscription_checkout_updated_webhook):
    webhooks = [subscription_checkout_updated_webhook]
    event_type = WebhookEventAsyncType.CHECKOUT_UPDATED
    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)
    deliveries = create_deliveries_for_subscriptions(event_type, checkout, webhooks)
    expected_payload = json.dumps({"checkout": {"id": checkout_id}, "meta": None})

    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_page_created(page, subscription_page_created_webhook):
    # given
    webhooks = [subscription_page_created_webhook]
    event_type = WebhookEventAsyncType.PAGE_CREATED
    expected_payload = json.dumps(generate_page_payload(page))

    # when
    deliveries = create_deliveries_for_subscriptions(event_type, page, webhooks)

    # then
    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_page_updated(page, subscription_page_updated_webhook):
    # given
    webhooks = [subscription_page_updated_webhook]
    event_type = WebhookEventAsyncType.PAGE_UPDATED
    expected_payload = json.dumps(generate_page_payload(page))

    # when
    deliveries = create_deliveries_for_subscriptions(event_type, page, webhooks)

    # then
    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_page_deleted(page, subscription_page_deleted_webhook):
    # given
    webhooks = [subscription_page_deleted_webhook]
    event_type = WebhookEventAsyncType.PAGE_DELETED
    expected_payload = json.dumps(generate_page_payload(page))

    # when
    deliveries = create_deliveries_for_subscriptions(event_type, page, webhooks)

    # then
    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_product_created_multiple_events_in_subscription(
    product, subscription_product_created_multiple_events_webhook
):
    webhooks = [subscription_product_created_multiple_events_webhook]
    event_type = WebhookEventAsyncType.PRODUCT_CREATED
    product_id = graphene.Node.to_global_id("Product", product.id)
    deliveries = create_deliveries_for_subscriptions(event_type, product, webhooks)
    expected_payload = json.dumps({"product": {"id": product_id}, "meta": None})

    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_warehouse_created(warehouse, subscription_warehouse_created_webhook):
    # given
    webhooks = [subscription_warehouse_created_webhook]
    event_type = WebhookEventAsyncType.WAREHOUSE_CREATED
    warehouse_id = graphene.Node.to_global_id("Warehouse", warehouse.id)

    # when
    deliveries = create_deliveries_for_subscriptions(event_type, warehouse, webhooks)

    # then
    expected_payload = generate_warehouse_payload(warehouse, warehouse_id)

    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_warehouse_updated(warehouse, subscription_warehouse_updated_webhook):
    # given
    webhooks = [subscription_warehouse_updated_webhook]
    event_type = WebhookEventAsyncType.WAREHOUSE_UPDATED
    voucher_id = graphene.Node.to_global_id("Warehouse", warehouse.id)

    # when
    deliveries = create_deliveries_for_subscriptions(event_type, warehouse, webhooks)

    # then
    expected_payload = generate_warehouse_payload(warehouse, voucher_id)
    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_warehouse_deleted(warehouse, subscription_warehouse_deleted_webhook):
    # given
    webhooks = [subscription_warehouse_deleted_webhook]

    warehouse_id = warehouse.id
    warehouse.delete()
    warehouse.id = warehouse_id
    warehouse.is_object_deleted = True

    event_type = WebhookEventAsyncType.WAREHOUSE_DELETED
    warehouse_global_id = graphene.Node.to_global_id("Warehouse", warehouse.id)

    # when
    deliveries = create_deliveries_for_subscriptions(event_type, warehouse, webhooks)

    # then
    expected_payload = generate_warehouse_payload(warehouse, warehouse_global_id)

    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_voucher_created(voucher, subscription_voucher_created_webhook):
    # given
    webhooks = [subscription_voucher_created_webhook]
    event_type = WebhookEventAsyncType.VOUCHER_CREATED
    voucher_id = graphene.Node.to_global_id("Voucher", voucher.id)

    # when
    deliveries = create_deliveries_for_subscriptions(event_type, voucher, webhooks)

    # then
    expected_payload = generate_voucher_payload(voucher, voucher_id)
    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_voucher_updated(voucher, subscription_voucher_updated_webhook):
    # given
    webhooks = [subscription_voucher_updated_webhook]
    event_type = WebhookEventAsyncType.VOUCHER_UPDATED
    voucher_id = graphene.Node.to_global_id("Voucher", voucher.id)

    # when
    deliveries = create_deliveries_for_subscriptions(event_type, voucher, webhooks)

    # then
    expected_payload = generate_voucher_payload(voucher, voucher_id)
    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_voucher_deleted(voucher, subscription_voucher_deleted_webhook):
    # given
    webhooks = [subscription_voucher_deleted_webhook]

    voucher_id = voucher.id
    voucher.delete()
    voucher.id = voucher_id

    event_type = WebhookEventAsyncType.VOUCHER_DELETED
    voucher_global_id = graphene.Node.to_global_id("Voucher", voucher.id)

    # when
    deliveries = create_deliveries_for_subscriptions(event_type, voucher, webhooks)

    # then
    expected_payload = generate_voucher_payload(voucher, voucher_global_id)
    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


@patch.object(logger, "info")
def test_create_deliveries_for_subscriptions_unsubscribable_event(
    mocked_logger, product, subscription_product_updated_webhook, any_webhook
):
    webhooks = [subscription_product_updated_webhook]
    event_type = "unsubscribable_type"

    deliveries = create_deliveries_for_subscriptions(event_type, product, webhooks)

    mocked_logger.assert_called_with(
        "Skipping subscription webhook. Event %s is not subscribable.", event_type
    )
    assert len(deliveries) == 0


@patch("saleor.graphql.webhook.subscription_payload.get_default_backend")
@patch.object(logger, "warning")
def test_create_deliveries_for_subscriptions_document_executed_with_error(
    mocked_task_logger,
    mocked_backend,
    product,
    subscription_product_updated_webhook,
):
    # given
    webhooks = [subscription_product_updated_webhook]
    event_type = WebhookEventAsyncType.ORDER_CREATED
    mocked_backend.document_from_string.execute.errors = "errors"
    # when
    deliveries = create_deliveries_for_subscriptions(event_type, product, webhooks)
    # then
    mocked_task_logger.assert_called_with(
        f"No payload was generated with subscription for event: {event_type}"
    )
    assert len(deliveries) == 0


def test_validate_subscription_query_valid():
    result = validate_subscription_query(
        subscription_queries.TEST_VALID_SUBSCRIPTION_QUERY
    )
    assert result is True


def test_validate_subscription_query_invalid():
    result = validate_subscription_query("invalid_query")
    assert result is False


def test_validate_subscription_query_valid_with_fragment():
    result = validate_subscription_query(
        subscription_queries.TEST_VALID_SUBSCRIPTION_QUERY_WITH_FRAGMENT
    )
    assert result is True


def test_validate_invalid_query_and_subscription():
    result = validate_subscription_query(
        subscription_queries.TEST_INVALID_QUERY_AND_SUBSCRIPTION
    )
    assert result is False


def test_validate_invalid_subscription_and_query():
    result = validate_subscription_query(
        subscription_queries.TEST_INVALID_SUBSCRIPTION_AND_QUERY
    )
    assert result is False


def test_validate_invalid_multiple_subscriptions():
    result = validate_subscription_query(
        subscription_queries.TEST_INVALID_MULTIPLE_SUBSCRIPTION
    )
    assert result is False
