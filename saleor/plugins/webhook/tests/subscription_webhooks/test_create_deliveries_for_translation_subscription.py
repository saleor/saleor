import json

import graphene

from .....webhook.event_types import WebhookEventAsyncType
from ...tasks import create_deliveries_for_subscriptions


def test_translation_created_product(
    product_translation_fr, subscription_translation_created_webhook
):
    webhooks = [subscription_translation_created_webhook]
    event_type = WebhookEventAsyncType.TRANSLATION_CREATED
    translation_id = graphene.Node.to_global_id(
        "ProductTranslation", product_translation_fr.id
    )
    deliveries = create_deliveries_for_subscriptions(
        event_type, product_translation_fr, webhooks
    )

    expected_payload = json.dumps({"translation": {"id": translation_id}})

    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_translation_created_product_variant(
    variant_translation_fr, subscription_translation_created_webhook
):
    webhooks = [subscription_translation_created_webhook]
    event_type = WebhookEventAsyncType.TRANSLATION_CREATED
    translation_id = graphene.Node.to_global_id(
        "ProductVariantTranslation", variant_translation_fr.id
    )
    deliveries = create_deliveries_for_subscriptions(
        event_type, variant_translation_fr, webhooks
    )

    expected_payload = json.dumps({"translation": {"id": translation_id}})

    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_translation_created_collection(
    collection_translation_fr, subscription_translation_created_webhook
):
    webhooks = [subscription_translation_created_webhook]
    event_type = WebhookEventAsyncType.TRANSLATION_CREATED
    translation_id = graphene.Node.to_global_id(
        "CollectionTranslation", collection_translation_fr.id
    )
    deliveries = create_deliveries_for_subscriptions(
        event_type, collection_translation_fr, webhooks
    )

    expected_payload = json.dumps({"translation": {"id": translation_id}})

    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_translation_created_category(
    category_translation_fr, subscription_translation_created_webhook
):
    webhooks = [subscription_translation_created_webhook]
    event_type = WebhookEventAsyncType.TRANSLATION_CREATED
    translation_id = graphene.Node.to_global_id(
        "CategoryTranslation", category_translation_fr.id
    )
    deliveries = create_deliveries_for_subscriptions(
        event_type, category_translation_fr, webhooks
    )

    expected_payload = json.dumps({"translation": {"id": translation_id}})

    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_translation_created_attribute(
    translated_attribute, subscription_translation_created_webhook
):
    webhooks = [subscription_translation_created_webhook]
    event_type = WebhookEventAsyncType.TRANSLATION_CREATED
    translation_id = graphene.Node.to_global_id(
        "AttributeTranslation", translated_attribute.id
    )
    deliveries = create_deliveries_for_subscriptions(
        event_type, translated_attribute, webhooks
    )

    expected_payload = json.dumps({"translation": {"id": translation_id}})

    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_translation_created_attribute_value(
    translated_attribute_value, subscription_translation_created_webhook
):
    webhooks = [subscription_translation_created_webhook]
    event_type = WebhookEventAsyncType.TRANSLATION_CREATED
    translation_id = graphene.Node.to_global_id(
        "AttributeValueTranslation", translated_attribute_value.id
    )
    deliveries = create_deliveries_for_subscriptions(
        event_type, translated_attribute_value, webhooks
    )

    expected_payload = json.dumps({"translation": {"id": translation_id}})

    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_translation_created_page(
    page_translation_fr, subscription_translation_created_webhook
):
    webhooks = [subscription_translation_created_webhook]
    event_type = WebhookEventAsyncType.TRANSLATION_CREATED
    translation_id = graphene.Node.to_global_id(
        "PageTranslation", page_translation_fr.id
    )
    deliveries = create_deliveries_for_subscriptions(
        event_type, page_translation_fr, webhooks
    )

    expected_payload = json.dumps({"translation": {"id": translation_id}})

    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_translation_created_shipping_method(
    shipping_method_translation_fr, subscription_translation_created_webhook
):
    webhooks = [subscription_translation_created_webhook]
    event_type = WebhookEventAsyncType.TRANSLATION_CREATED
    translation_id = graphene.Node.to_global_id(
        "ShippingMethodTranslation", shipping_method_translation_fr.id
    )
    deliveries = create_deliveries_for_subscriptions(
        event_type, shipping_method_translation_fr, webhooks
    )

    expected_payload = json.dumps({"translation": {"id": translation_id}})

    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_translation_created_sale(
    sale_translation_fr, subscription_translation_created_webhook
):
    webhooks = [subscription_translation_created_webhook]
    event_type = WebhookEventAsyncType.TRANSLATION_CREATED
    translation_id = graphene.Node.to_global_id(
        "SaleTranslation", sale_translation_fr.id
    )
    deliveries = create_deliveries_for_subscriptions(
        event_type, sale_translation_fr, webhooks
    )

    expected_payload = json.dumps({"translation": {"id": translation_id}})

    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_translation_created_voucher(
    voucher_translation_fr, subscription_translation_created_webhook
):
    webhooks = [subscription_translation_created_webhook]
    event_type = WebhookEventAsyncType.TRANSLATION_CREATED
    translation_id = graphene.Node.to_global_id(
        "VoucherTranslation", voucher_translation_fr.id
    )
    deliveries = create_deliveries_for_subscriptions(
        event_type, voucher_translation_fr, webhooks
    )

    expected_payload = json.dumps({"translation": {"id": translation_id}})

    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_translation_created_menu_item(
    menu_item_translation_fr, subscription_translation_created_webhook
):
    webhooks = [subscription_translation_created_webhook]
    event_type = WebhookEventAsyncType.TRANSLATION_CREATED
    translation_id = graphene.Node.to_global_id(
        "MenuItemTranslation", menu_item_translation_fr.id
    )
    deliveries = create_deliveries_for_subscriptions(
        event_type, menu_item_translation_fr, webhooks
    )

    expected_payload = json.dumps({"translation": {"id": translation_id}})

    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_translation_updated_product(
    product_translation_fr, subscription_translation_updated_webhook
):
    webhooks = [subscription_translation_updated_webhook]
    event_type = WebhookEventAsyncType.TRANSLATION_UPDATED
    translation_id = graphene.Node.to_global_id(
        "ProductTranslation", product_translation_fr.id
    )
    deliveries = create_deliveries_for_subscriptions(
        event_type, product_translation_fr, webhooks
    )

    expected_payload = json.dumps({"translation": {"id": translation_id}})

    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_translation_updated_product_variant(
    variant_translation_fr, subscription_translation_updated_webhook
):
    webhooks = [subscription_translation_updated_webhook]
    event_type = WebhookEventAsyncType.TRANSLATION_UPDATED
    translation_id = graphene.Node.to_global_id(
        "ProductVariantTranslation", variant_translation_fr.id
    )
    deliveries = create_deliveries_for_subscriptions(
        event_type, variant_translation_fr, webhooks
    )

    expected_payload = json.dumps({"translation": {"id": translation_id}})

    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_translation_updated_collection(
    collection_translation_fr, subscription_translation_updated_webhook
):
    webhooks = [subscription_translation_updated_webhook]
    event_type = WebhookEventAsyncType.TRANSLATION_UPDATED
    translation_id = graphene.Node.to_global_id(
        "CollectionTranslation", collection_translation_fr.id
    )
    deliveries = create_deliveries_for_subscriptions(
        event_type, collection_translation_fr, webhooks
    )

    expected_payload = json.dumps({"translation": {"id": translation_id}})

    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_translation_updated_category(
    category_translation_fr, subscription_translation_updated_webhook
):
    webhooks = [subscription_translation_updated_webhook]
    event_type = WebhookEventAsyncType.TRANSLATION_UPDATED
    translation_id = graphene.Node.to_global_id(
        "CategoryTranslation", category_translation_fr.id
    )
    deliveries = create_deliveries_for_subscriptions(
        event_type, category_translation_fr, webhooks
    )

    expected_payload = json.dumps({"translation": {"id": translation_id}})

    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_translation_updated_attribute(
    translated_attribute, subscription_translation_updated_webhook
):
    webhooks = [subscription_translation_updated_webhook]
    event_type = WebhookEventAsyncType.TRANSLATION_UPDATED
    translation_id = graphene.Node.to_global_id(
        "AttributeTranslation", translated_attribute.id
    )
    deliveries = create_deliveries_for_subscriptions(
        event_type, translated_attribute, webhooks
    )

    expected_payload = json.dumps({"translation": {"id": translation_id}})

    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_translation_updated_attribute_value(
    translated_attribute_value, subscription_translation_updated_webhook
):
    webhooks = [subscription_translation_updated_webhook]
    event_type = WebhookEventAsyncType.TRANSLATION_UPDATED
    translation_id = graphene.Node.to_global_id(
        "AttributeValueTranslation", translated_attribute_value.id
    )
    deliveries = create_deliveries_for_subscriptions(
        event_type, translated_attribute_value, webhooks
    )

    expected_payload = json.dumps({"translation": {"id": translation_id}})

    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_translation_updated_page(
    page_translation_fr, subscription_translation_updated_webhook
):
    webhooks = [subscription_translation_updated_webhook]
    event_type = WebhookEventAsyncType.TRANSLATION_UPDATED
    translation_id = graphene.Node.to_global_id(
        "PageTranslation", page_translation_fr.id
    )
    deliveries = create_deliveries_for_subscriptions(
        event_type, page_translation_fr, webhooks
    )

    expected_payload = json.dumps({"translation": {"id": translation_id}})

    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_translation_updated_shipping_method(
    shipping_method_translation_fr, subscription_translation_updated_webhook
):
    webhooks = [subscription_translation_updated_webhook]
    event_type = WebhookEventAsyncType.TRANSLATION_UPDATED
    translation_id = graphene.Node.to_global_id(
        "ShippingMethodTranslation", shipping_method_translation_fr.id
    )
    deliveries = create_deliveries_for_subscriptions(
        event_type, shipping_method_translation_fr, webhooks
    )

    expected_payload = json.dumps({"translation": {"id": translation_id}})

    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_translation_updated_sale(
    sale_translation_fr, subscription_translation_updated_webhook
):
    webhooks = [subscription_translation_updated_webhook]
    event_type = WebhookEventAsyncType.TRANSLATION_UPDATED
    translation_id = graphene.Node.to_global_id(
        "SaleTranslation", sale_translation_fr.id
    )
    deliveries = create_deliveries_for_subscriptions(
        event_type, sale_translation_fr, webhooks
    )

    expected_payload = json.dumps({"translation": {"id": translation_id}})

    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_translation_updated_voucher(
    voucher_translation_fr, subscription_translation_updated_webhook
):
    webhooks = [subscription_translation_updated_webhook]
    event_type = WebhookEventAsyncType.TRANSLATION_UPDATED
    translation_id = graphene.Node.to_global_id(
        "VoucherTranslation", voucher_translation_fr.id
    )
    deliveries = create_deliveries_for_subscriptions(
        event_type, voucher_translation_fr, webhooks
    )

    expected_payload = json.dumps({"translation": {"id": translation_id}})

    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_translation_updated_menu_item(
    menu_item_translation_fr, subscription_translation_updated_webhook
):
    webhooks = [subscription_translation_updated_webhook]
    event_type = WebhookEventAsyncType.TRANSLATION_UPDATED
    translation_id = graphene.Node.to_global_id(
        "MenuItemTranslation", menu_item_translation_fr.id
    )
    deliveries = create_deliveries_for_subscriptions(
        event_type, menu_item_translation_fr, webhooks
    )

    expected_payload = json.dumps({"translation": {"id": translation_id}})

    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]
