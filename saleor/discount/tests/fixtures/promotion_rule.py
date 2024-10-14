from decimal import Decimal

import graphene
import pytest

from ....tests.utils import dummy_editorjs
from ... import RewardType, RewardValueType
from ...interface import VariantPromotionRuleInfo
from ...models import PromotionRule


@pytest.fixture
def promotion_rule(channel_USD, catalogue_promotion, product):
    rule = PromotionRule.objects.create(
        name="Promotion rule name",
        promotion=catalogue_promotion,
        description=dummy_editorjs("Test description for percentage promotion rule."),
        catalogue_predicate={
            "productPredicate": {
                "ids": [graphene.Node.to_global_id("Product", product.id)]
            }
        },
        reward_value_type=RewardValueType.PERCENTAGE,
        reward_value=Decimal("25"),
    )
    rule.channels.add(channel_USD)
    return rule


@pytest.fixture
def order_promotion_rule(channel_USD, order_promotion_without_rules):
    rule = PromotionRule.objects.create(
        name="Order promotion rule",
        promotion=order_promotion_without_rules,
        order_predicate={
            "discountedObjectPredicate": {"baseSubtotalPrice": {"range": {"gte": 20}}}
        },
        reward_value_type=RewardValueType.PERCENTAGE,
        reward_value=Decimal("25"),
        reward_type=RewardType.SUBTOTAL_DISCOUNT,
    )
    rule.channels.add(channel_USD)
    return rule


@pytest.fixture
def gift_promotion_rule(channel_USD, order_promotion_without_rules, product_list):
    rule = PromotionRule.objects.create(
        name="Order promotion rule",
        promotion=order_promotion_without_rules,
        order_predicate={
            "discountedObjectPredicate": {"baseSubtotalPrice": {"range": {"gte": 20}}}
        },
        reward_type=RewardType.GIFT,
    )
    rule.channels.add(channel_USD)
    rule.gifts.set([product.variants.first() for product in product_list[:2]])
    return rule


@pytest.fixture
def rule_info(
    promotion_rule,
    promotion_translation_fr,
    promotion_rule_translation_fr,
    variant,
    channel_USD,
):
    variant_channel_listing = variant.channel_listings.get(channel_id=channel_USD.id)
    listing_promotion_rule = variant_channel_listing.variantlistingpromotionrule.create(
        promotion_rule=promotion_rule,
        discount_amount=Decimal("10"),
        currency=channel_USD.currency_code,
    )
    return VariantPromotionRuleInfo(
        rule=promotion_rule,
        promotion=promotion_rule.promotion,
        variant_listing_promotion_rule=listing_promotion_rule,
        promotion_translation=promotion_translation_fr,
        rule_translation=promotion_rule_translation_fr,
    )


@pytest.fixture
def catalogue_predicate(product, category, collection, variant):
    collection_id = graphene.Node.to_global_id("Collection", collection.id)
    category_id = graphene.Node.to_global_id("Category", category.id)
    product_id = graphene.Node.to_global_id("Product", product.id)
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    return {
        "OR": [
            {"collectionPredicate": {"ids": [collection_id]}},
            {"categoryPredicate": {"ids": [category_id]}},
            {"productPredicate": {"ids": [product_id]}},
            {"variantPredicate": {"ids": [variant_id]}},
        ]
    }
