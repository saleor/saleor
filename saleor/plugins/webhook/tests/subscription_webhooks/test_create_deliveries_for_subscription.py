import json
from unittest.mock import patch

import graphene
import pytest
from freezegun import freeze_time

from .....channel.models import Channel
from .....giftcard.models import GiftCard
from .....graphql.webhook.subscription_query import SubscriptionQuery
from .....menu.models import Menu, MenuItem
from .....product.models import Category
from .....shipping.models import ShippingMethod, ShippingZone
from .....webhook.event_types import WebhookEventAsyncType, WebhookEventSyncType
from ...tasks import create_deliveries_for_subscriptions, logger
from . import subscription_queries
from .payloads import (
    generate_address_payload,
    generate_app_payload,
    generate_attribute_payload,
    generate_attribute_value_payload,
    generate_category_payload,
    generate_collection_payload,
    generate_customer_payload,
    generate_fulfillment_payload,
    generate_gift_card_payload,
    generate_invoice_payload,
    generate_menu_item_payload,
    generate_menu_payload,
    generate_page_payload,
    generate_page_type_payload,
    generate_permission_group_payload,
    generate_sale_payload,
    generate_shipping_method_payload,
    generate_staff_payload,
    generate_voucher_created_payload_with_meta,
    generate_voucher_payload,
    generate_warehouse_payload,
)


@freeze_time("2022-05-12 12:00:00")
@pytest.mark.parametrize("requestor_type", ["user", "app", "anonymous"])
def test_subscription_query_with_meta(
    requestor_type,
    voucher,
    staff_user,
    app_with_token,
    subscription_voucher_webhook_with_meta,
):
    # given
    requestor_map = {
        "user": staff_user,
        "app": app_with_token,
        "anonymous": None,
    }
    webhooks = [subscription_voucher_webhook_with_meta]
    event_type = WebhookEventAsyncType.VOUCHER_CREATED
    voucher_id = graphene.Node.to_global_id("Voucher", voucher.id)

    requestor = requestor_map[requestor_type]

    # when
    deliveries = create_deliveries_for_subscriptions(
        event_type, voucher, webhooks, requestor
    )

    # then
    expected_payload = generate_voucher_created_payload_with_meta(
        voucher,
        voucher_id,
        requestor,
        requestor_type,
        subscription_voucher_webhook_with_meta.app,
    )
    assert json.loads(deliveries[0].payload.payload) == json.loads(expected_payload)
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_address_created(address, subscription_address_created_webhook):
    # given
    webhooks = [subscription_address_created_webhook]
    event_type = WebhookEventAsyncType.ADDRESS_CREATED

    # when
    deliveries = create_deliveries_for_subscriptions(event_type, address, webhooks)

    # then
    expected_payload = json.dumps({"address": generate_address_payload(address)})

    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_address_updated(address, subscription_address_updated_webhook):
    # given
    webhooks = [subscription_address_updated_webhook]
    event_type = WebhookEventAsyncType.ADDRESS_UPDATED

    # when
    deliveries = create_deliveries_for_subscriptions(event_type, address, webhooks)

    # then
    expected_payload = json.dumps({"address": generate_address_payload(address)})
    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_address_deleted(address, subscription_address_deleted_webhook):
    # given
    webhooks = [subscription_address_deleted_webhook]

    id = address.id
    address.delete()
    address.id = id

    event_type = WebhookEventAsyncType.ADDRESS_DELETED

    # when
    deliveries = create_deliveries_for_subscriptions(event_type, address, webhooks)

    # then
    expected_payload = json.dumps({"address": generate_address_payload(address)})
    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_app_installed(app, subscription_app_installed_webhook):
    # given
    webhooks = [subscription_app_installed_webhook]
    event_type = WebhookEventAsyncType.APP_INSTALLED
    app_id = graphene.Node.to_global_id("App", app.id)

    # when
    deliveries = create_deliveries_for_subscriptions(event_type, app, webhooks)

    # then
    expected_payload = generate_app_payload(app, app_id)
    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_app_updated(app, subscription_app_updated_webhook):
    # given
    webhooks = [subscription_app_updated_webhook]
    event_type = WebhookEventAsyncType.APP_UPDATED
    app_id = graphene.Node.to_global_id("App", app.id)

    # when
    deliveries = create_deliveries_for_subscriptions(event_type, app, webhooks)

    # then
    expected_payload = generate_app_payload(app, app_id)
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
    expected_payload = generate_app_payload(app, app_id)
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
    expected_payload = generate_app_payload(app, app_id)
    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_attribute_created(color_attribute, subscription_attribute_created_webhook):
    # given
    webhooks = [subscription_attribute_created_webhook]
    event_type = WebhookEventAsyncType.ATTRIBUTE_CREATED

    # when
    deliveries = create_deliveries_for_subscriptions(
        event_type, color_attribute, webhooks
    )

    # then
    expected_payload = generate_attribute_payload(color_attribute)
    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_attribute_updated(color_attribute, subscription_attribute_updated_webhook):
    # given
    webhooks = [subscription_attribute_updated_webhook]
    event_type = WebhookEventAsyncType.ATTRIBUTE_UPDATED

    # when
    deliveries = create_deliveries_for_subscriptions(
        event_type, color_attribute, webhooks
    )

    # then
    expected_payload = generate_attribute_payload(color_attribute)
    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_attribute_deleted(color_attribute, subscription_attribute_deleted_webhook):
    # given
    webhooks = [subscription_attribute_deleted_webhook]

    id = color_attribute.id
    color_attribute.delete()
    color_attribute.id = id

    event_type = WebhookEventAsyncType.ATTRIBUTE_DELETED

    # when
    deliveries = create_deliveries_for_subscriptions(
        event_type, color_attribute, webhooks
    )

    # then
    expected_payload = generate_attribute_payload(color_attribute)
    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_attribute_value_created(
    pink_attribute_value, subscription_attribute_value_created_webhook
):
    # given
    webhooks = [subscription_attribute_value_created_webhook]
    event_type = WebhookEventAsyncType.ATTRIBUTE_VALUE_CREATED

    # when
    deliveries = create_deliveries_for_subscriptions(
        event_type, pink_attribute_value, webhooks
    )

    # then
    expected_payload = generate_attribute_value_payload(pink_attribute_value)
    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_attribute_value_updated(
    pink_attribute_value, subscription_attribute_value_updated_webhook
):
    # given
    webhooks = [subscription_attribute_value_updated_webhook]
    event_type = WebhookEventAsyncType.ATTRIBUTE_VALUE_UPDATED

    # when
    deliveries = create_deliveries_for_subscriptions(
        event_type, pink_attribute_value, webhooks
    )

    # then
    expected_payload = generate_attribute_value_payload(pink_attribute_value)
    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_attribute_value_deleted(
    pink_attribute_value, subscription_attribute_value_deleted_webhook
):
    # given
    webhooks = [subscription_attribute_value_deleted_webhook]

    id = pink_attribute_value.id
    pink_attribute_value.delete()
    pink_attribute_value.id = id

    event_type = WebhookEventAsyncType.ATTRIBUTE_VALUE_DELETED

    # when
    deliveries = create_deliveries_for_subscriptions(
        event_type, pink_attribute_value, webhooks
    )

    # then
    expected_payload = generate_attribute_value_payload(pink_attribute_value)
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
    expected_payload = json.dumps({"category": {"id": category_id}})
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
    expected_payload = json.dumps({"channel": {"id": channel_id}})
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
    expected_payload = json.dumps({"channel": {"id": channel_id}})
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
    expected_payload = json.dumps({"channel": {"id": channel_id}})
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
    expected_payload = json.dumps({"channel": {"id": channel_id, "isActive": status}})
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


def test_gift_card_metadata_updated(
    gift_card, subscription_gift_card_metadata_updated_webhook
):
    # given
    webhooks = [subscription_gift_card_metadata_updated_webhook]
    event_type = WebhookEventAsyncType.GIFT_CARD_METADATA_UPDATED
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
        {"shippingMethod": {"id": shipping_method_id, "name": shipping_method.name}}
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
            }
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
            }
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
        }
    )
    assert zones_instances[0].id is not None
    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_shipping_zone_metadata_updated(
    shipping_zone, subscription_shipping_zone_metadata_updated_webhook
):
    # given
    webhooks = [subscription_shipping_zone_metadata_updated_webhook]
    event_type = WebhookEventAsyncType.SHIPPING_ZONE_METADATA_UPDATED
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
            }
        }
    )
    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_staff_created(staff_user, subscription_staff_created_webhook):
    # given
    webhooks = [subscription_staff_created_webhook]
    event_type = WebhookEventAsyncType.STAFF_CREATED
    expected_payload = json.dumps(generate_staff_payload(staff_user))

    # when
    deliveries = create_deliveries_for_subscriptions(event_type, staff_user, webhooks)

    # then
    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_staff_updated(staff_user, subscription_staff_updated_webhook):
    # given
    webhooks = [subscription_staff_updated_webhook]
    event_type = WebhookEventAsyncType.STAFF_UPDATED
    expected_payload = json.dumps(generate_staff_payload(staff_user))

    # when
    deliveries = create_deliveries_for_subscriptions(event_type, staff_user, webhooks)

    # then
    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_staff_deleted(staff_user, subscription_staff_deleted_webhook):
    # given
    webhooks = [subscription_staff_deleted_webhook]
    id = staff_user.id
    staff_user.delete()
    staff_user.id = id

    event_type = WebhookEventAsyncType.STAFF_DELETED

    # when
    deliveries = create_deliveries_for_subscriptions(event_type, staff_user, webhooks)
    expected_payload = json.dumps(generate_staff_payload(staff_user))

    # then

    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_product_created(product, subscription_product_created_webhook):
    webhooks = [subscription_product_created_webhook]
    event_type = WebhookEventAsyncType.PRODUCT_CREATED
    product_id = graphene.Node.to_global_id("Product", product.id)
    deliveries = create_deliveries_for_subscriptions(event_type, product, webhooks)
    expected_payload = json.dumps({"product": {"id": product_id}})

    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_product_updated(product, subscription_product_updated_webhook):
    webhooks = [subscription_product_updated_webhook]
    event_type = WebhookEventAsyncType.PRODUCT_UPDATED
    product_id = graphene.Node.to_global_id("Product", product.id)
    deliveries = create_deliveries_for_subscriptions(event_type, product, webhooks)
    expected_payload = json.dumps({"product": {"id": product_id}})

    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_product_deleted(product, subscription_product_deleted_webhook):
    webhooks = [subscription_product_deleted_webhook]
    event_type = WebhookEventAsyncType.PRODUCT_DELETED
    product_id = graphene.Node.to_global_id("Product", product.id)
    deliveries = create_deliveries_for_subscriptions(event_type, product, webhooks)
    expected_payload = json.dumps({"product": {"id": product_id}})

    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_product_metadata_updated(
    product, subscription_product_metadata_updated_webhook
):
    webhooks = [subscription_product_metadata_updated_webhook]
    event_type = WebhookEventAsyncType.PRODUCT_METADATA_UPDATED
    product_id = graphene.Node.to_global_id("Product", product.id)
    deliveries = create_deliveries_for_subscriptions(event_type, product, webhooks)
    expected_payload = json.dumps({"product": {"id": product_id}})

    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_product_variant_created(variant, subscription_product_variant_created_webhook):
    webhooks = [subscription_product_variant_created_webhook]
    event_type = WebhookEventAsyncType.PRODUCT_VARIANT_CREATED
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    deliveries = create_deliveries_for_subscriptions(event_type, variant, webhooks)
    expected_payload = json.dumps({"productVariant": {"id": variant_id}})

    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_product_variant_updated(variant, subscription_product_variant_updated_webhook):
    webhooks = [subscription_product_variant_updated_webhook]
    event_type = WebhookEventAsyncType.PRODUCT_VARIANT_UPDATED
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    deliveries = create_deliveries_for_subscriptions(event_type, variant, webhooks)
    expected_payload = json.dumps({"productVariant": {"id": variant_id}})

    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_product_variant_deleted(variant, subscription_product_variant_deleted_webhook):
    webhooks = [subscription_product_variant_deleted_webhook]
    event_type = WebhookEventAsyncType.PRODUCT_VARIANT_DELETED
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    deliveries = create_deliveries_for_subscriptions(event_type, variant, webhooks)
    expected_payload = json.dumps({"productVariant": {"id": variant_id}})

    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_product_variant_metadata_updated(
    variant, subscription_product_variant_metadata_updated_webhook
):
    webhooks = [subscription_product_variant_metadata_updated_webhook]
    event_type = WebhookEventAsyncType.PRODUCT_VARIANT_METADATA_UPDATED
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    deliveries = create_deliveries_for_subscriptions(event_type, variant, webhooks)
    expected_payload = json.dumps({"productVariant": {"id": variant_id}})

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
    expected_payload = json.dumps({"productVariant": {"id": variant_id}})

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
    expected_payload = json.dumps({"productVariant": {"id": variant_id}})

    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_product_variant_stock_updated(
    stock, subscription_product_variant_stock_updated_webhook
):
    webhooks = [subscription_product_variant_stock_updated_webhook]
    event_type = WebhookEventAsyncType.PRODUCT_VARIANT_STOCK_UPDATED
    variant_id = graphene.Node.to_global_id("ProductVariant", stock.product_variant.id)
    warehouse_id = graphene.Node.to_global_id("Warehouse", stock.warehouse.id)
    deliveries = create_deliveries_for_subscriptions(event_type, stock, webhooks)
    expected_payload = json.dumps(
        {
            "productVariant": {"id": variant_id},
            "warehouse": {"id": warehouse_id},
        }
    )

    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_order_created(order, subscription_order_created_webhook):
    webhooks = [subscription_order_created_webhook]
    event_type = WebhookEventAsyncType.ORDER_CREATED
    order_id = graphene.Node.to_global_id("Order", order.id)
    deliveries = create_deliveries_for_subscriptions(event_type, order, webhooks)
    expected_payload = json.dumps({"order": {"id": order_id}})

    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_order_confirmed(order, subscription_order_confirmed_webhook):
    webhooks = [subscription_order_confirmed_webhook]
    event_type = WebhookEventAsyncType.ORDER_CONFIRMED
    order_id = graphene.Node.to_global_id("Order", order.id)
    deliveries = create_deliveries_for_subscriptions(event_type, order, webhooks)
    expected_payload = json.dumps({"order": {"id": order_id}})

    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_order_fully_paid(order, subscription_order_fully_paid_webhook):
    webhooks = [subscription_order_fully_paid_webhook]
    event_type = WebhookEventAsyncType.ORDER_FULLY_PAID
    order_id = graphene.Node.to_global_id("Order", order.id)
    deliveries = create_deliveries_for_subscriptions(event_type, order, webhooks)
    expected_payload = json.dumps({"order": {"id": order_id}})

    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_order_updated(order, subscription_order_updated_webhook):
    webhooks = [subscription_order_updated_webhook]
    event_type = WebhookEventAsyncType.ORDER_UPDATED
    order_id = graphene.Node.to_global_id("Order", order.id)
    deliveries = create_deliveries_for_subscriptions(event_type, order, webhooks)
    expected_payload = json.dumps({"order": {"id": order_id}})

    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_order_cancelled(order, subscription_order_cancelled_webhook):
    webhooks = [subscription_order_cancelled_webhook]
    event_type = WebhookEventAsyncType.ORDER_CANCELLED
    order_id = graphene.Node.to_global_id("Order", order.id)
    deliveries = create_deliveries_for_subscriptions(event_type, order, webhooks)
    expected_payload = json.dumps({"order": {"id": order_id}})

    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_order_fulfilled(order, subscription_order_fulfilled_webhook):
    webhooks = [subscription_order_fulfilled_webhook]
    event_type = WebhookEventAsyncType.ORDER_FULFILLED
    order_id = graphene.Node.to_global_id("Order", order.id)
    deliveries = create_deliveries_for_subscriptions(event_type, order, webhooks)
    expected_payload = json.dumps({"order": {"id": order_id}})

    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_order_metadata_updated(order, subscription_order_metadata_updated_webhook):
    webhooks = [subscription_order_metadata_updated_webhook]
    event_type = WebhookEventAsyncType.ORDER_METADATA_UPDATED
    order_id = graphene.Node.to_global_id("Order", order.id)
    deliveries = create_deliveries_for_subscriptions(event_type, order, webhooks)
    expected_payload = json.dumps({"order": {"id": order_id}})

    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_draft_order_created(order, subscription_draft_order_created_webhook):
    webhooks = [subscription_draft_order_created_webhook]
    event_type = WebhookEventAsyncType.DRAFT_ORDER_CREATED
    order_id = graphene.Node.to_global_id("Order", order.id)
    deliveries = create_deliveries_for_subscriptions(event_type, order, webhooks)
    expected_payload = json.dumps({"order": {"id": order_id}})

    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_draft_order_updated(order, subscription_draft_order_updated_webhook):
    webhooks = [subscription_draft_order_updated_webhook]
    event_type = WebhookEventAsyncType.DRAFT_ORDER_UPDATED
    order_id = graphene.Node.to_global_id("Order", order.id)
    deliveries = create_deliveries_for_subscriptions(event_type, order, webhooks)
    expected_payload = json.dumps({"order": {"id": order_id}})

    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_draft_order_deleted(order, subscription_draft_order_deleted_webhook):
    webhooks = [subscription_draft_order_deleted_webhook]
    event_type = WebhookEventAsyncType.DRAFT_ORDER_DELETED
    order_id = graphene.Node.to_global_id("Order", order.id)
    deliveries = create_deliveries_for_subscriptions(event_type, order, webhooks)
    expected_payload = json.dumps({"order": {"id": order_id}})

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


def test_sale_toggle(sale, subscription_sale_toggle_webhook):
    # given
    webhooks = [subscription_sale_toggle_webhook]
    event_type = WebhookEventAsyncType.SALE_TOGGLE
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
    assert json.loads(deliveries[0].payload.payload) == expected_payload
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


def test_fulfillment_approved(fulfillment, subscription_fulfillment_approved_webhook):
    # given
    webhooks = [subscription_fulfillment_approved_webhook]
    event_type = WebhookEventAsyncType.FULFILLMENT_APPROVED
    expected_payload = generate_fulfillment_payload(fulfillment)

    # when
    deliveries = create_deliveries_for_subscriptions(event_type, fulfillment, webhooks)

    # then
    assert deliveries[0].payload.payload == json.dumps(expected_payload)
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_fulfillment_metadata_updated(
    fulfillment, subscription_fulfillment_metadata_updated_webhook
):
    # given
    webhooks = [subscription_fulfillment_metadata_updated_webhook]
    event_type = WebhookEventAsyncType.FULFILLMENT_METADATA_UPDATED
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


def test_customer_deleted(customer_user, subscription_customer_created_webhook):
    # given
    customer_user_id = customer_user.id
    customer_user.delete()
    customer_user.id = customer_user_id

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


def test_customer_metadata_updated(
    customer_user, subscription_customer_metadata_updated_webhook
):
    # given
    webhooks = [subscription_customer_metadata_updated_webhook]
    event_type = WebhookEventAsyncType.CUSTOMER_METADATA_UPDATED
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


def test_collection_metadata_updated(
    collection_with_products, subscription_collection_metadata_updated_webhook
):
    # given
    webhooks = [subscription_collection_metadata_updated_webhook]
    collection = collection_with_products[0].collections.first()
    event_type = WebhookEventAsyncType.COLLECTION_METADATA_UPDATED
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
    expected_payload = json.dumps(
        {"checkout": {"id": checkout_id, "totalPrice": {"currency": "USD"}}}
    )
    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_checkout_update(checkout, subscription_checkout_updated_webhook):
    webhooks = [subscription_checkout_updated_webhook]
    event_type = WebhookEventAsyncType.CHECKOUT_UPDATED
    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)
    deliveries = create_deliveries_for_subscriptions(event_type, checkout, webhooks)
    expected_payload = json.dumps({"checkout": {"id": checkout_id}})

    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_checkout_metadata_updated(
    checkout, subscription_checkout_metadata_updated_webhook
):
    webhooks = [subscription_checkout_metadata_updated_webhook]
    event_type = WebhookEventAsyncType.CHECKOUT_METADATA_UPDATED
    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)
    deliveries = create_deliveries_for_subscriptions(event_type, checkout, webhooks)
    expected_payload = json.dumps({"checkout": {"id": checkout_id}})

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


def test_page_type_created(page_type, subscription_page_type_created_webhook):
    # given
    webhooks = [subscription_page_type_created_webhook]
    event_type = WebhookEventAsyncType.PAGE_TYPE_CREATED
    expected_payload = json.dumps(generate_page_type_payload(page_type))

    # when
    deliveries = create_deliveries_for_subscriptions(event_type, page_type, webhooks)

    # then
    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_page_type_updated(page_type, subscription_page_type_updated_webhook):
    # given
    webhooks = [subscription_page_type_updated_webhook]
    event_type = WebhookEventAsyncType.PAGE_TYPE_UPDATED
    expected_payload = json.dumps(generate_page_type_payload(page_type))

    # when
    deliveries = create_deliveries_for_subscriptions(event_type, page_type, webhooks)

    # then
    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_page_type_deleted(page_type, subscription_page_type_deleted_webhook):
    # given
    page_type_id = page_type.id
    page_type.delete()
    page_type.id = page_type_id

    webhooks = [subscription_page_type_deleted_webhook]
    event_type = WebhookEventAsyncType.PAGE_TYPE_DELETED
    expected_payload = json.dumps(generate_page_type_payload(page_type))

    # when
    deliveries = create_deliveries_for_subscriptions(event_type, page_type, webhooks)

    # then
    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_permission_group_created(
    permission_group_manage_users, subscription_permission_group_created_webhook
):
    # given
    group = permission_group_manage_users
    webhooks = [subscription_permission_group_created_webhook]
    event_type = WebhookEventAsyncType.PERMISSION_GROUP_CREATED
    expected_payload = json.dumps(generate_permission_group_payload(group))

    # when
    deliveries = create_deliveries_for_subscriptions(event_type, group, webhooks)

    # then
    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_permission_group_updated(
    permission_group_manage_users, subscription_permission_group_updated_webhook
):
    # given
    group = permission_group_manage_users
    webhooks = [subscription_permission_group_updated_webhook]
    event_type = WebhookEventAsyncType.PERMISSION_GROUP_UPDATED
    expected_payload = json.dumps(generate_permission_group_payload(group))

    # when
    deliveries = create_deliveries_for_subscriptions(event_type, group, webhooks)

    # then
    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_permission_group_deleted(
    permission_group_manage_users, subscription_permission_group_deleted_webhook
):
    # given
    group = permission_group_manage_users
    group_id = group.id
    group.delete()
    group.id = group_id

    webhooks = [subscription_permission_group_deleted_webhook]
    event_type = WebhookEventAsyncType.PERMISSION_GROUP_DELETED
    expected_payload = json.dumps(generate_permission_group_payload(group))

    # when
    deliveries = create_deliveries_for_subscriptions(event_type, group, webhooks)

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
    expected_payload = json.dumps({"product": {"id": product_id}})

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
    warehouse_id = graphene.Node.to_global_id("Warehouse", warehouse.id)

    # when
    deliveries = create_deliveries_for_subscriptions(event_type, warehouse, webhooks)

    # then
    expected_payload = generate_warehouse_payload(warehouse, warehouse_id)
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


def test_warehouse_metadata_updated(
    warehouse, subscription_warehouse_metadata_updated_webhook
):
    # given
    webhooks = [subscription_warehouse_metadata_updated_webhook]
    event_type = WebhookEventAsyncType.WAREHOUSE_METADATA_UPDATED
    warehouse_id = graphene.Node.to_global_id("Warehouse", warehouse.id)

    # when
    deliveries = create_deliveries_for_subscriptions(event_type, warehouse, webhooks)

    # then
    expected_payload = generate_warehouse_payload(warehouse, warehouse_id)
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


def test_voucher_metadata_updated(
    voucher, subscription_voucher_metadata_updated_webhook
):
    # given
    webhooks = [subscription_voucher_metadata_updated_webhook]
    event_type = WebhookEventAsyncType.VOUCHER_METADATA_UPDATED
    voucher_id = graphene.Node.to_global_id("Voucher", voucher.id)

    # when
    deliveries = create_deliveries_for_subscriptions(event_type, voucher, webhooks)

    # then
    expected_payload = generate_voucher_payload(voucher, voucher_id)
    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_transaction_item_metadata_updated(
    transaction_item, subscription_transaction_item_metadata_updated_webhook
):
    # given
    webhooks = [subscription_transaction_item_metadata_updated_webhook]
    event_type = WebhookEventAsyncType.TRANSACTION_ITEM_METADATA_UPDATED
    transaction_item_id = graphene.Node.to_global_id(
        "TransactionItem", transaction_item.id
    )

    # when
    deliveries = create_deliveries_for_subscriptions(
        event_type, transaction_item, webhooks
    )

    # then
    expected_payload = json.dumps({"transaction": {"id": transaction_item_id}})
    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_shipping_list_methods_for_checkout(
    checkout_with_shipping_required,
    subscription_shipping_list_methods_for_checkout_webhook,
    address,
    shipping_method,
):
    # given
    checkout = checkout_with_shipping_required
    checkout.shipping_address = address
    checkout.shipping_method = shipping_method
    webhooks = [subscription_shipping_list_methods_for_checkout_webhook]
    event_type = WebhookEventSyncType.SHIPPING_LIST_METHODS_FOR_CHECKOUT
    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)
    all_shipping_methods = ShippingMethod.objects.all()
    # when
    deliveries = create_deliveries_for_subscriptions(event_type, checkout, webhooks)
    # then
    shipping_methods = [
        {
            "id": graphene.Node.to_global_id("ShippingMethod", sm.pk),
            "name": sm.name,
        }
        for sm in all_shipping_methods
    ]
    payload = json.loads(deliveries[0].payload.payload)

    assert payload["checkout"] == {"id": checkout_id}
    for method in shipping_methods:
        assert method in payload["shippingMethods"]
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_checkout_filter_shipping_methods(
    checkout_with_shipping_required,
    subscription_checkout_filter_shipping_methods_webhook,
    address,
    shipping_method,
):
    # given
    checkout = checkout_with_shipping_required
    checkout.shipping_address = address
    checkout.shipping_method = shipping_method
    webhooks = [subscription_checkout_filter_shipping_methods_webhook]
    event_type = WebhookEventSyncType.CHECKOUT_FILTER_SHIPPING_METHODS
    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)
    all_shipping_methods = ShippingMethod.objects.all()
    # when
    deliveries = create_deliveries_for_subscriptions(event_type, checkout, webhooks)
    # then
    shipping_methods = [
        {
            "id": graphene.Node.to_global_id("ShippingMethod", sm.pk),
            "name": sm.name,
        }
        for sm in all_shipping_methods
    ]
    payload = json.loads(deliveries[0].payload.payload)

    assert payload["checkout"] == {"id": checkout_id}
    for method in shipping_methods:
        assert method in payload["shippingMethods"]
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_checkout_filter_shipping_methods_no_methods_in_channel(
    checkout,
    subscription_checkout_filter_shipping_methods_webhook,
    address,
    shipping_method,
    shipping_method_channel_PLN,
):
    # given
    webhooks = [subscription_checkout_filter_shipping_methods_webhook]
    event_type = WebhookEventSyncType.CHECKOUT_FILTER_SHIPPING_METHODS
    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)

    # when
    deliveries = create_deliveries_for_subscriptions(event_type, checkout, webhooks)

    # then
    expected_payload = {"checkout": {"id": checkout_id}, "shippingMethods": []}
    assert json.loads(deliveries[0].payload.payload) == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_checkout_filter_shipping_methods_with_circular_call_for_shipping_methods(
    checkout_ready_to_complete,
    subscription_checkout_filter_shipping_method_webhook_with_shipping_methods,
):

    # given
    webhooks = [
        subscription_checkout_filter_shipping_method_webhook_with_shipping_methods
    ]
    event_type = WebhookEventSyncType.CHECKOUT_FILTER_SHIPPING_METHODS

    # when
    deliveries = create_deliveries_for_subscriptions(
        event_type, checkout_ready_to_complete, webhooks
    )

    # then
    payload = json.loads(deliveries[0].payload.payload)

    assert len(payload["errors"]) == 1
    assert (
        payload["errors"][0]["message"]
        == "Resolving this field is not allowed in synchronous events."
    )
    assert payload["checkout"] is None


def test_checkout_filter_shipping_methods_with_available_shipping_methods_field(
    checkout_ready_to_complete,
    subscription_checkout_filter_shipping_method_webhook_with_available_ship_methods,
):

    # given
    webhooks = [
        subscription_checkout_filter_shipping_method_webhook_with_available_ship_methods
    ]
    event_type = WebhookEventSyncType.CHECKOUT_FILTER_SHIPPING_METHODS

    # when
    deliveries = create_deliveries_for_subscriptions(
        event_type, checkout_ready_to_complete, webhooks
    )

    # then
    payload = json.loads(deliveries[0].payload.payload)

    assert len(payload["errors"]) == 1
    assert (
        payload["errors"][0]["message"]
        == "Resolving this field is not allowed in synchronous events."
    )
    assert payload["checkout"] is None


def test_checkout_filter_shipping_methods_with_circular_call_for_available_gateways(
    checkout_ready_to_complete,
    subscription_checkout_filter_shipping_method_webhook_with_payment_gateways,
):

    # given
    webhooks = [
        subscription_checkout_filter_shipping_method_webhook_with_payment_gateways
    ]
    event_type = WebhookEventSyncType.CHECKOUT_FILTER_SHIPPING_METHODS

    # when
    deliveries = create_deliveries_for_subscriptions(
        event_type, checkout_ready_to_complete, webhooks
    )

    # then
    payload = json.loads(deliveries[0].payload.payload)

    assert len(payload["errors"]) == 1
    assert (
        payload["errors"][0]["message"]
        == "Resolving this field is not allowed in synchronous events."
    )
    assert payload["checkout"] is None


def test_order_filter_shipping_methods(
    order_line_with_one_allocation,
    subscription_order_filter_shipping_methods_webhook,
    address,
):
    # given
    order = order_line_with_one_allocation.order
    order_line_with_one_allocation.is_shipping_required = True
    order_line_with_one_allocation.save(update_fields=["is_shipping_required"])

    order.currency = "USD"
    order.shipping_address = address
    order.save(update_fields=["shipping_address"])
    webhooks = [subscription_order_filter_shipping_methods_webhook]
    event_type = WebhookEventSyncType.ORDER_FILTER_SHIPPING_METHODS
    order_id = graphene.Node.to_global_id("Order", order.pk)
    all_shipping_methods = ShippingMethod.objects.all()

    # when
    deliveries = create_deliveries_for_subscriptions(event_type, order, webhooks)
    # then
    shipping_methods = [
        {
            "id": graphene.Node.to_global_id("ShippingMethod", sm.pk),
            "name": sm.name,
        }
        for sm in all_shipping_methods
    ]
    payload = json.loads(deliveries[0].payload.payload)

    assert payload["order"] == {"id": order_id}
    for method in shipping_methods:
        assert method in payload["shippingMethods"]
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_order_filter_shipping_methods_no_methods_in_channel(
    order_line_with_one_allocation,
    subscription_order_filter_shipping_methods_webhook,
    shipping_method_channel_PLN,
):
    # given
    order = order_line_with_one_allocation.order
    order.save(update_fields=["shipping_address"])
    webhooks = [subscription_order_filter_shipping_methods_webhook]
    event_type = WebhookEventSyncType.ORDER_FILTER_SHIPPING_METHODS
    order_id = graphene.Node.to_global_id("Order", order.pk)

    # when
    deliveries = create_deliveries_for_subscriptions(event_type, order, webhooks)

    # then
    expected_payload = {"order": {"id": order_id}, "shippingMethods": []}

    assert json.loads(deliveries[0].payload.payload) == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_order_filter_shipping_methods_with_circular_call_for_available_methods(
    order_line_with_one_allocation,
    subscription_order_filter_shipping_methods_webhook_with_available_ship_methods,
):

    # given
    webhooks = [
        subscription_order_filter_shipping_methods_webhook_with_available_ship_methods
    ]
    event_type = WebhookEventSyncType.ORDER_FILTER_SHIPPING_METHODS
    order = order_line_with_one_allocation.order

    # when
    deliveries = create_deliveries_for_subscriptions(event_type, order, webhooks)

    # then
    payload = json.loads(deliveries[0].payload.payload)

    assert len(payload["errors"]) == 1
    assert (
        payload["errors"][0]["message"]
        == "Resolving this field is not allowed in synchronous events."
    )


def test_order_filter_shipping_methods_with_circular_call_for_shipping_methods(
    order_line_with_one_allocation,
    subscription_order_filter_shipping_methods_webhook_with_shipping_methods,
):

    # given
    webhooks = [
        subscription_order_filter_shipping_methods_webhook_with_shipping_methods
    ]
    event_type = WebhookEventSyncType.ORDER_FILTER_SHIPPING_METHODS
    order = order_line_with_one_allocation.order

    # when
    deliveries = create_deliveries_for_subscriptions(event_type, order, webhooks)

    # then
    payload = json.loads(deliveries[0].payload.payload)

    assert len(payload["errors"]) == 1
    assert (
        payload["errors"][0]["message"]
        == "Resolving this field is not allowed in synchronous events."
    )
    assert payload["order"] is None


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
    query = SubscriptionQuery(subscription_queries.TEST_VALID_SUBSCRIPTION_QUERY)
    assert query.is_valid


def test_validate_subscription_query_invalid():
    query = SubscriptionQuery("invalid_query")
    assert not query.is_valid


def test_validate_subscription_query_valid_with_fragment():
    query = SubscriptionQuery(
        subscription_queries.TEST_VALID_SUBSCRIPTION_QUERY_WITH_FRAGMENT
    )
    assert query.is_valid


def test_validate_invalid_query_and_subscription():
    query = SubscriptionQuery(subscription_queries.TEST_INVALID_QUERY_AND_SUBSCRIPTION)
    assert not query.is_valid
    assert (
        "This anonymous operation must be the only defined operation" in query.error_msg
    )


def test_validate_invalid_subscription_and_query():
    query = SubscriptionQuery(subscription_queries.TEST_INVALID_SUBSCRIPTION_AND_QUERY)
    assert not query.is_valid
    assert (
        "This anonymous operation must be the only defined operation" in query.error_msg
    )


def test_validate_invalid_multiple_subscriptions():
    query = SubscriptionQuery(subscription_queries.TEST_INVALID_MULTIPLE_SUBSCRIPTION)
    assert not query.is_valid
    assert (
        "This anonymous operation must be the only defined operation" in query.error_msg
    )


def test_validate_valid_multiple_events_in_subscription():
    query = SubscriptionQuery(subscription_queries.INVALID_MULTIPLE_EVENTS)
    assert query.is_valid


def test_validate_invalid_multiple_events_and_fragments_in_subscription():
    query = SubscriptionQuery(
        subscription_queries.INVALID_MULTIPLE_EVENTS_WITH_FRAGMENTS
    )
    assert query.is_valid


def test_validate_query_with_multiple_fragments():
    query = SubscriptionQuery(subscription_queries.QUERY_WITH_MULTIPLE_FRAGMENTS)
    assert query.is_valid


def test_generate_payload_from_subscription_return_permission_errors_in_payload(
    gift_card, subscription_gift_card_created_webhook, permission_manage_gift_card
):
    # given
    subscription_gift_card_created_webhook.app.permissions.remove(
        permission_manage_gift_card
    )
    webhooks = [subscription_gift_card_created_webhook]

    # when
    deliveries = create_deliveries_for_subscriptions(
        WebhookEventAsyncType.GIFT_CARD_CREATED, gift_card, webhooks
    )

    # then
    payload = json.loads(deliveries[0].payload.payload)
    error_code = "PermissionDenied"

    assert not payload["giftCard"]
    assert payload["errors"][0]["extensions"]["exception"]["code"] == error_code
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]
