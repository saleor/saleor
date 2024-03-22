import json

import graphene

from .....webhook.event_types import WebhookEventAsyncType
from .....webhook.transport.asynchronous.transport import (
    create_deliveries_for_subscriptions,
)


def test_translation_created_product(
    product_translation_fr, subscription_product_translation_created_webhook
):
    webhooks = [subscription_product_translation_created_webhook]
    event_type = WebhookEventAsyncType.TRANSLATION_CREATED
    translation_id = graphene.Node.to_global_id(
        "ProductTranslation", product_translation_fr.id
    )
    product = product_translation_fr.product
    product_id = graphene.Node.to_global_id("Product", product.id)
    deliveries = create_deliveries_for_subscriptions(
        event_type, product_translation_fr, webhooks
    )

    expected_payload = json.dumps(
        {
            "translation": {
                "id": translation_id,
                "name": product_translation_fr.name,
                "translatableContent": {
                    "productId": product_id,
                    "name": product.name,
                },
            }
        }
    )

    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_translation_created_product_variant(
    variant_translation_fr, subscription_product_variant_translation_created_webhook
):
    webhooks = [subscription_product_variant_translation_created_webhook]
    event_type = WebhookEventAsyncType.TRANSLATION_CREATED
    translation_id = graphene.Node.to_global_id(
        "ProductVariantTranslation", variant_translation_fr.id
    )
    variant = variant_translation_fr.product_variant
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    deliveries = create_deliveries_for_subscriptions(
        event_type, variant_translation_fr, webhooks
    )

    expected_payload = json.dumps(
        {
            "translation": {
                "id": translation_id,
                "name": variant_translation_fr.name,
                "translatableContent": {
                    "productVariantId": variant_id,
                    "name": variant.name,
                },
            }
        }
    )

    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_translation_created_collection(
    collection_translation_fr, subscription_collection_translation_created_webhook
):
    webhooks = [subscription_collection_translation_created_webhook]
    event_type = WebhookEventAsyncType.TRANSLATION_CREATED
    translation_id = graphene.Node.to_global_id(
        "CollectionTranslation", collection_translation_fr.id
    )
    collection = collection_translation_fr.collection
    collection_id = graphene.Node.to_global_id("Collection", collection.id)
    deliveries = create_deliveries_for_subscriptions(
        event_type, collection_translation_fr, webhooks
    )

    expected_payload = json.dumps(
        {
            "translation": {
                "id": translation_id,
                "name": collection_translation_fr.name,
                "translatableContent": {
                    "collectionId": collection_id,
                    "name": collection.name,
                },
            }
        }
    )

    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_translation_created_category(
    category_translation_fr, subscription_category_translation_created_webhook
):
    webhooks = [subscription_category_translation_created_webhook]
    event_type = WebhookEventAsyncType.TRANSLATION_CREATED
    translation_id = graphene.Node.to_global_id(
        "CategoryTranslation", category_translation_fr.id
    )
    category = category_translation_fr.category
    category_id = graphene.Node.to_global_id("Category", category.id)
    deliveries = create_deliveries_for_subscriptions(
        event_type, category_translation_fr, webhooks
    )

    expected_payload = json.dumps(
        {
            "translation": {
                "id": translation_id,
                "name": category_translation_fr.name,
                "translatableContent": {
                    "categoryId": category_id,
                    "name": category.name,
                },
            }
        }
    )

    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_translation_created_attribute(
    translated_attribute, subscription_attribute_translation_created_webhook
):
    webhooks = [subscription_attribute_translation_created_webhook]
    event_type = WebhookEventAsyncType.TRANSLATION_CREATED
    translation_id = graphene.Node.to_global_id(
        "AttributeTranslation", translated_attribute.id
    )
    attribute = translated_attribute.attribute
    attribute_id = graphene.Node.to_global_id("Attribute", attribute.id)
    deliveries = create_deliveries_for_subscriptions(
        event_type, translated_attribute, webhooks
    )

    expected_payload = json.dumps(
        {
            "translation": {
                "id": translation_id,
                "name": translated_attribute.name,
                "translatableContent": {
                    "attributeId": attribute_id,
                    "name": attribute.name,
                },
            }
        }
    )

    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_translation_created_attribute_value(
    translated_attribute_value, subscription_attribute_value_translation_created_webhook
):
    webhooks = [subscription_attribute_value_translation_created_webhook]
    event_type = WebhookEventAsyncType.TRANSLATION_CREATED
    translation_id = graphene.Node.to_global_id(
        "AttributeValueTranslation", translated_attribute_value.id
    )
    attribute_value = translated_attribute_value.attribute_value
    attribute_value_id = graphene.Node.to_global_id(
        "AttributeValue", attribute_value.id
    )
    deliveries = create_deliveries_for_subscriptions(
        event_type, translated_attribute_value, webhooks
    )

    expected_payload = json.dumps(
        {
            "translation": {
                "id": translation_id,
                "name": translated_attribute_value.name,
                "translatableContent": {
                    "attributeValueId": attribute_value_id,
                    "name": attribute_value.name,
                },
            }
        }
    )

    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_translation_created_page(
    page_translation_fr, subscription_page_translation_created_webhook
):
    webhooks = [subscription_page_translation_created_webhook]
    event_type = WebhookEventAsyncType.TRANSLATION_CREATED
    translation_id = graphene.Node.to_global_id(
        "PageTranslation", page_translation_fr.id
    )
    page = page_translation_fr.page
    page_id = graphene.Node.to_global_id("Page", page.id)
    deliveries = create_deliveries_for_subscriptions(
        event_type, page_translation_fr, webhooks
    )

    expected_payload = json.dumps(
        {
            "translation": {
                "id": translation_id,
                "title": page_translation_fr.title,
                "translatableContent": {
                    "pageId": page_id,
                    "title": page.title,
                },
            }
        }
    )

    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_translation_created_shipping_method(
    shipping_method_translation_fr,
    subscription_shipping_method_translation_created_webhook,
):
    webhooks = [subscription_shipping_method_translation_created_webhook]
    event_type = WebhookEventAsyncType.TRANSLATION_CREATED
    translation_id = graphene.Node.to_global_id(
        "ShippingMethodTranslation", shipping_method_translation_fr.id
    )
    shipping_method = shipping_method_translation_fr.shipping_method
    shipping_method_id = graphene.Node.to_global_id(
        "ShippingMethodType", shipping_method.id
    )
    deliveries = create_deliveries_for_subscriptions(
        event_type, shipping_method_translation_fr, webhooks
    )

    expected_payload = json.dumps(
        {
            "translation": {
                "id": translation_id,
                "name": shipping_method_translation_fr.name,
                "translatableContent": {
                    "shippingMethodId": shipping_method_id,
                    "name": shipping_method.name,
                },
            }
        }
    )

    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_translation_created_promotion(
    promotion_translation_fr, subscription_promotion_translation_created_webhook
):
    webhooks = [subscription_promotion_translation_created_webhook]
    event_type = WebhookEventAsyncType.TRANSLATION_CREATED
    translation_id = graphene.Node.to_global_id(
        "PromotionTranslation", promotion_translation_fr.id
    )
    promotion = promotion_translation_fr.promotion
    promotion_id = graphene.Node.to_global_id("Promotion", promotion.id)
    deliveries = create_deliveries_for_subscriptions(
        event_type, promotion_translation_fr, webhooks
    )

    expected_payload = json.dumps(
        {
            "translation": {
                "id": translation_id,
                "name": promotion_translation_fr.name,
                "translatableContent": {
                    "promotionId": promotion_id,
                    "name": promotion.name,
                },
            }
        }
    )

    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_translation_created_promotion_converted_from_sale(
    promotion_converted_from_sale_translation_fr,
    subscription_sale_translation_created_webhook,
):
    translation = promotion_converted_from_sale_translation_fr
    webhooks = [subscription_sale_translation_created_webhook]
    event_type = WebhookEventAsyncType.TRANSLATION_CREATED
    translation_id = graphene.Node.to_global_id("SaleTranslation", translation.id)
    promotion = promotion_converted_from_sale_translation_fr.promotion
    promotion_id = graphene.Node.to_global_id("Sale", promotion.old_sale_id)
    deliveries = create_deliveries_for_subscriptions(event_type, translation, webhooks)

    expected_payload = json.dumps(
        {
            "translation": {
                "__typename": "SaleTranslation",
                "id": translation_id,
                "name": promotion_converted_from_sale_translation_fr.name,
                "translatableContent": {
                    "saleId": promotion_id,
                    "name": promotion.name,
                },
            }
        }
    )

    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_translation_created_promotion_rule(
    promotion_rule_translation_fr,
    subscription_promotion_rule_translation_created_webhook,
):
    webhooks = [subscription_promotion_rule_translation_created_webhook]
    event_type = WebhookEventAsyncType.TRANSLATION_CREATED
    translation_id = graphene.Node.to_global_id(
        "PromotionRuleTranslation", promotion_rule_translation_fr.id
    )
    promotion_rule = promotion_rule_translation_fr.promotion_rule
    promotion_rule_id = graphene.Node.to_global_id("PromotionRule", promotion_rule.id)
    deliveries = create_deliveries_for_subscriptions(
        event_type, promotion_rule_translation_fr, webhooks
    )

    expected_payload = json.dumps(
        {
            "translation": {
                "id": translation_id,
                "name": promotion_rule_translation_fr.name,
                "translatableContent": {
                    "promotionRuleId": promotion_rule_id,
                    "name": promotion_rule.name,
                },
            }
        }
    )

    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_translation_created_voucher(
    voucher_translation_fr, subscription_voucher_translation_created_webhook
):
    webhooks = [subscription_voucher_translation_created_webhook]
    event_type = WebhookEventAsyncType.TRANSLATION_CREATED
    translation_id = graphene.Node.to_global_id(
        "VoucherTranslation", voucher_translation_fr.id
    )
    voucher = voucher_translation_fr.voucher
    voucher_id = graphene.Node.to_global_id("Voucher", voucher.id)
    deliveries = create_deliveries_for_subscriptions(
        event_type, voucher_translation_fr, webhooks
    )

    expected_payload = json.dumps(
        {
            "translation": {
                "id": translation_id,
                "name": voucher_translation_fr.name,
                "translatableContent": {
                    "voucherId": voucher_id,
                    "name": voucher.name,
                },
            }
        }
    )

    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_translation_created_menu_item(
    menu_item_translation_fr, subscription_menu_item_translation_created_webhook
):
    webhooks = [subscription_menu_item_translation_created_webhook]
    event_type = WebhookEventAsyncType.TRANSLATION_CREATED
    translation_id = graphene.Node.to_global_id(
        "MenuItemTranslation", menu_item_translation_fr.id
    )
    menu_item = menu_item_translation_fr.menu_item
    menu_item_id = graphene.Node.to_global_id("MenuItem", menu_item.id)
    deliveries = create_deliveries_for_subscriptions(
        event_type, menu_item_translation_fr, webhooks
    )

    expected_payload = json.dumps(
        {
            "translation": {
                "id": translation_id,
                "name": menu_item_translation_fr.name,
                "translatableContent": {
                    "menuItemId": menu_item_id,
                    "name": menu_item.name,
                },
            }
        }
    )

    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_translation_updated_product(
    product_translation_fr, subscription_product_translation_updated_webhook
):
    webhooks = [subscription_product_translation_updated_webhook]
    event_type = WebhookEventAsyncType.TRANSLATION_UPDATED
    translation_id = graphene.Node.to_global_id(
        "ProductTranslation", product_translation_fr.id
    )
    product = product_translation_fr.product
    product_id = graphene.Node.to_global_id("Product", product.id)
    deliveries = create_deliveries_for_subscriptions(
        event_type, product_translation_fr, webhooks
    )

    expected_payload = json.dumps(
        {
            "translation": {
                "id": translation_id,
                "name": product_translation_fr.name,
                "translatableContent": {
                    "productId": product_id,
                    "name": product.name,
                },
            }
        }
    )

    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_translation_updated_product_variant(
    variant_translation_fr, subscription_product_variant_translation_updated_webhook
):
    webhooks = [subscription_product_variant_translation_updated_webhook]
    event_type = WebhookEventAsyncType.TRANSLATION_UPDATED
    translation_id = graphene.Node.to_global_id(
        "ProductVariantTranslation", variant_translation_fr.id
    )
    variant = variant_translation_fr.product_variant
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    deliveries = create_deliveries_for_subscriptions(
        event_type, variant_translation_fr, webhooks
    )

    expected_payload = json.dumps(
        {
            "translation": {
                "id": translation_id,
                "name": variant_translation_fr.name,
                "translatableContent": {
                    "productVariantId": variant_id,
                    "name": variant.name,
                },
            }
        }
    )

    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_translation_updated_collection(
    collection_translation_fr, subscription_collection_translation_updated_webhook
):
    webhooks = [subscription_collection_translation_updated_webhook]
    event_type = WebhookEventAsyncType.TRANSLATION_UPDATED
    translation_id = graphene.Node.to_global_id(
        "CollectionTranslation", collection_translation_fr.id
    )
    collection = collection_translation_fr.collection
    collection_id = graphene.Node.to_global_id("Collection", collection.id)
    deliveries = create_deliveries_for_subscriptions(
        event_type, collection_translation_fr, webhooks
    )

    expected_payload = json.dumps(
        {
            "translation": {
                "id": translation_id,
                "name": collection_translation_fr.name,
                "translatableContent": {
                    "collectionId": collection_id,
                    "name": collection.name,
                },
            }
        }
    )

    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_translation_updated_category(
    category_translation_fr, subscription_category_translation_updated_webhook
):
    webhooks = [subscription_category_translation_updated_webhook]
    event_type = WebhookEventAsyncType.TRANSLATION_UPDATED
    translation_id = graphene.Node.to_global_id(
        "CategoryTranslation", category_translation_fr.id
    )
    category = category_translation_fr.category
    category_id = graphene.Node.to_global_id("Category", category.id)
    deliveries = create_deliveries_for_subscriptions(
        event_type, category_translation_fr, webhooks
    )

    expected_payload = json.dumps(
        {
            "translation": {
                "id": translation_id,
                "name": category_translation_fr.name,
                "translatableContent": {
                    "categoryId": category_id,
                    "name": category.name,
                },
            }
        }
    )

    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_translation_updated_attribute(
    translated_attribute, subscription_attribute_translation_updated_webhook
):
    webhooks = [subscription_attribute_translation_updated_webhook]
    event_type = WebhookEventAsyncType.TRANSLATION_UPDATED
    translation_id = graphene.Node.to_global_id(
        "AttributeTranslation", translated_attribute.id
    )
    attribute = translated_attribute.attribute
    attribute_id = graphene.Node.to_global_id("Attribute", attribute.id)
    deliveries = create_deliveries_for_subscriptions(
        event_type, translated_attribute, webhooks
    )

    expected_payload = json.dumps(
        {
            "translation": {
                "id": translation_id,
                "name": translated_attribute.name,
                "translatableContent": {
                    "attributeId": attribute_id,
                    "name": attribute.name,
                },
            }
        }
    )

    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_translation_updated_attribute_value(
    translated_attribute_value, subscription_attribute_value_translation_updated_webhook
):
    webhooks = [subscription_attribute_value_translation_updated_webhook]
    event_type = WebhookEventAsyncType.TRANSLATION_UPDATED
    translation_id = graphene.Node.to_global_id(
        "AttributeValueTranslation", translated_attribute_value.id
    )
    attribute_value = translated_attribute_value.attribute_value
    attribute_value_id = graphene.Node.to_global_id(
        "AttributeValue", attribute_value.id
    )
    deliveries = create_deliveries_for_subscriptions(
        event_type, translated_attribute_value, webhooks
    )

    expected_payload = json.dumps(
        {
            "translation": {
                "id": translation_id,
                "name": translated_attribute_value.name,
                "translatableContent": {
                    "attributeValueId": attribute_value_id,
                    "name": attribute_value.name,
                },
            }
        }
    )

    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_translation_updated_page(
    page_translation_fr, subscription_page_translation_updated_webhook
):
    webhooks = [subscription_page_translation_updated_webhook]
    event_type = WebhookEventAsyncType.TRANSLATION_UPDATED
    translation_id = graphene.Node.to_global_id(
        "PageTranslation", page_translation_fr.id
    )
    page = page_translation_fr.page
    page_id = graphene.Node.to_global_id("Page", page.id)
    deliveries = create_deliveries_for_subscriptions(
        event_type, page_translation_fr, webhooks
    )

    expected_payload = json.dumps(
        {
            "translation": {
                "id": translation_id,
                "title": page_translation_fr.title,
                "translatableContent": {
                    "pageId": page_id,
                    "title": page.title,
                },
            }
        }
    )

    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_translation_updated_shipping_method(
    shipping_method_translation_fr,
    subscription_shipping_method_translation_updated_webhook,
):
    webhooks = [subscription_shipping_method_translation_updated_webhook]
    event_type = WebhookEventAsyncType.TRANSLATION_UPDATED
    translation_id = graphene.Node.to_global_id(
        "ShippingMethodTranslation", shipping_method_translation_fr.id
    )
    shipping_method = shipping_method_translation_fr.shipping_method
    shipping_method_id = graphene.Node.to_global_id(
        "ShippingMethodType", shipping_method.id
    )
    deliveries = create_deliveries_for_subscriptions(
        event_type, shipping_method_translation_fr, webhooks
    )

    expected_payload = json.dumps(
        {
            "translation": {
                "id": translation_id,
                "name": shipping_method_translation_fr.name,
                "translatableContent": {
                    "shippingMethodId": shipping_method_id,
                    "name": shipping_method.name,
                },
            }
        }
    )

    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_translation_updated_promotion(
    promotion_translation_fr, subscription_promotion_translation_updated_webhook
):
    webhooks = [subscription_promotion_translation_updated_webhook]
    event_type = WebhookEventAsyncType.TRANSLATION_UPDATED
    translation_id = graphene.Node.to_global_id(
        "PromotionTranslation", promotion_translation_fr.id
    )
    promotion = promotion_translation_fr.promotion
    promotion_id = graphene.Node.to_global_id("Promotion", promotion.id)
    deliveries = create_deliveries_for_subscriptions(
        event_type, promotion_translation_fr, webhooks
    )

    expected_payload = json.dumps(
        {
            "translation": {
                "id": translation_id,
                "name": promotion_translation_fr.name,
                "translatableContent": {
                    "promotionId": promotion_id,
                    "name": promotion.name,
                },
            }
        }
    )

    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_translation_updated_promotion_rule(
    promotion_rule_translation_fr,
    subscription_promotion_rule_translation_updated_webhook,
):
    webhooks = [subscription_promotion_rule_translation_updated_webhook]
    event_type = WebhookEventAsyncType.TRANSLATION_UPDATED
    translation_id = graphene.Node.to_global_id(
        "PromotionRuleTranslation", promotion_rule_translation_fr.id
    )
    promotion_rule = promotion_rule_translation_fr.promotion_rule
    promotion_rule_id = graphene.Node.to_global_id("PromotionRule", promotion_rule.id)
    deliveries = create_deliveries_for_subscriptions(
        event_type, promotion_rule_translation_fr, webhooks
    )

    expected_payload = json.dumps(
        {
            "translation": {
                "id": translation_id,
                "name": promotion_rule_translation_fr.name,
                "translatableContent": {
                    "promotionRuleId": promotion_rule_id,
                    "name": promotion_rule.name,
                },
            }
        }
    )

    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_translation_updated_voucher(
    voucher_translation_fr, subscription_voucher_translation_updated_webhook
):
    webhooks = [subscription_voucher_translation_updated_webhook]
    event_type = WebhookEventAsyncType.TRANSLATION_UPDATED
    translation_id = graphene.Node.to_global_id(
        "VoucherTranslation", voucher_translation_fr.id
    )
    voucher = voucher_translation_fr.voucher
    voucher_id = graphene.Node.to_global_id("Voucher", voucher.id)
    deliveries = create_deliveries_for_subscriptions(
        event_type, voucher_translation_fr, webhooks
    )

    expected_payload = json.dumps(
        {
            "translation": {
                "id": translation_id,
                "name": voucher_translation_fr.name,
                "translatableContent": {
                    "voucherId": voucher_id,
                    "name": voucher.name,
                },
            }
        }
    )

    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


def test_translation_updated_menu_item(
    menu_item_translation_fr, subscription_menu_item_translation_updated_webhook
):
    webhooks = [subscription_menu_item_translation_updated_webhook]
    event_type = WebhookEventAsyncType.TRANSLATION_UPDATED
    translation_id = graphene.Node.to_global_id(
        "MenuItemTranslation", menu_item_translation_fr.id
    )
    menu_item = menu_item_translation_fr.menu_item
    menu_item_id = graphene.Node.to_global_id("MenuItem", menu_item.id)
    deliveries = create_deliveries_for_subscriptions(
        event_type, menu_item_translation_fr, webhooks
    )

    expected_payload = json.dumps(
        {
            "translation": {
                "id": translation_id,
                "name": menu_item_translation_fr.name,
                "translatableContent": {
                    "menuItemId": menu_item_id,
                    "name": menu_item.name,
                },
            }
        }
    )

    assert deliveries[0].payload.payload == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]
