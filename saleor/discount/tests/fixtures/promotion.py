import datetime
from decimal import Decimal

import graphene
import pytest
from django.utils import timezone

from ....product.utils.variants import fetch_variants_for_promotion_rules
from ....tests.utils import dummy_editorjs
from ... import PromotionType, RewardType, RewardValueType
from ...models import Promotion, PromotionRule


@pytest.fixture
def catalogue_promotion(channel_USD, product, collection):
    promotion = Promotion.objects.create(
        name="Promotion",
        type=PromotionType.CATALOGUE,
        description=dummy_editorjs("Test description."),
        end_date=timezone.now() + datetime.timedelta(days=30),
    )
    rules = PromotionRule.objects.bulk_create(
        [
            PromotionRule(
                name="Percentage promotion rule",
                promotion=promotion,
                description=dummy_editorjs(
                    "Test description for percentage promotion rule."
                ),
                catalogue_predicate={
                    "productPredicate": {
                        "ids": [graphene.Node.to_global_id("Product", product.id)]
                    }
                },
                reward_value_type=RewardValueType.PERCENTAGE,
                reward_value=Decimal("10"),
            ),
            PromotionRule(
                name="Fixed promotion rule",
                promotion=promotion,
                description=dummy_editorjs(
                    "Test description for fixes promotion rule."
                ),
                catalogue_predicate={
                    "collectionPredicate": {
                        "ids": [graphene.Node.to_global_id("Collection", collection.id)]
                    }
                },
                reward_value_type=RewardValueType.FIXED,
                reward_value=Decimal("5"),
            ),
        ]
    )
    for rule in rules:
        rule.channels.add(channel_USD)
    fetch_variants_for_promotion_rules(promotion.rules.all())
    return promotion


@pytest.fixture
def catalogue_promotion_without_rules(db):
    promotion = Promotion.objects.create(
        name="Promotion",
        description=dummy_editorjs("Test description."),
        end_date=timezone.now() + datetime.timedelta(days=30),
        type=PromotionType.CATALOGUE,
    )
    return promotion


@pytest.fixture
def order_promotion_without_rules(db):
    promotion = Promotion.objects.create(
        name="Promotion",
        description=dummy_editorjs("Test description."),
        end_date=timezone.now() + datetime.timedelta(days=30),
        type=PromotionType.ORDER,
    )
    return promotion


@pytest.fixture
def catalogue_promotion_with_single_rule(catalogue_predicate, channel_USD):
    promotion = Promotion.objects.create(
        name="Promotion with single rule", type=PromotionType.CATALOGUE
    )
    rule = PromotionRule.objects.create(
        name="Sale rule",
        promotion=promotion,
        catalogue_predicate=catalogue_predicate,
        reward_value_type=RewardValueType.FIXED,
        reward_value=Decimal(5),
    )
    rule.channels.add(channel_USD)
    return promotion


@pytest.fixture
def order_promotion_with_rule(channel_USD):
    promotion = Promotion.objects.create(
        name="Promotion with order rule", type=PromotionType.ORDER
    )
    rule = PromotionRule.objects.create(
        name="Promotion rule",
        promotion=promotion,
        order_predicate={
            "discountedObjectPredicate": {"baseSubtotalPrice": {"range": {"gte": 100}}}
        },
        reward_value_type=RewardValueType.FIXED,
        reward_value=Decimal(5),
        reward_type=RewardType.SUBTOTAL_DISCOUNT,
    )
    rule.channels.add(channel_USD)
    return promotion


@pytest.fixture
def promotion_list(channel_USD, product, collection):
    collection.products.add(product)
    promotions = Promotion.objects.bulk_create(
        [
            Promotion(
                name="Promotion 1",
                type=PromotionType.CATALOGUE,
                description=dummy_editorjs("Promotion 1 description."),
                start_date=timezone.now() + datetime.timedelta(days=1),
                end_date=timezone.now() + datetime.timedelta(days=10),
            ),
            Promotion(
                name="Promotion 2",
                type=PromotionType.CATALOGUE,
                description=dummy_editorjs("Promotion 2 description."),
                start_date=timezone.now() + datetime.timedelta(days=5),
                end_date=timezone.now() + datetime.timedelta(days=20),
            ),
            Promotion(
                name="Promotion 3",
                type=PromotionType.CATALOGUE,
                description=dummy_editorjs("TePromotion 3 description."),
                start_date=timezone.now() + datetime.timedelta(days=15),
                end_date=timezone.now() + datetime.timedelta(days=30),
            ),
        ]
    )
    rules = PromotionRule.objects.bulk_create(
        [
            PromotionRule(
                name="Promotion 1 percentage rule",
                promotion=promotions[0],
                description=dummy_editorjs(
                    "Test description for promotion 1 percentage rule."
                ),
                catalogue_predicate={
                    "productPredicate": {
                        "ids": [graphene.Node.to_global_id("Product", product.id)]
                    }
                },
                reward_value_type=RewardValueType.PERCENTAGE,
                reward_value=Decimal("10"),
            ),
            PromotionRule(
                name="Promotion 1 fixed rule",
                promotion=promotions[0],
                description=dummy_editorjs(
                    "Test description for promotion 1 fixed rule."
                ),
                catalogue_predicate={
                    "collectionPredicate": {
                        "ids": [graphene.Node.to_global_id("Collection", collection.id)]
                    }
                },
                reward_value_type=RewardValueType.FIXED,
                reward_value=Decimal("5"),
            ),
            PromotionRule(
                name="Promotion 2 percentage rule",
                promotion=promotions[1],
                description=dummy_editorjs(
                    "Test description for promotion 2 percentage rule."
                ),
                catalogue_predicate={
                    "productPredicate": {
                        "ids": [graphene.Node.to_global_id("Product", product.id)]
                    }
                },
                reward_value_type=RewardValueType.PERCENTAGE,
                reward_value=Decimal("10"),
            ),
            PromotionRule(
                name="Promotion 3 fixed rule",
                promotion=promotions[2],
                description=dummy_editorjs(
                    "Test description for promotion 3 fixed rule."
                ),
                catalogue_predicate={
                    "collectionPredicate": {
                        "ids": [graphene.Node.to_global_id("Collection", collection.id)]
                    }
                },
                reward_value_type=RewardValueType.FIXED,
                reward_value=Decimal("5"),
            ),
        ]
    )
    for rule in rules:
        rule.channels.add(channel_USD)
    fetch_variants_for_promotion_rules(PromotionRule.objects.all())
    return promotions


@pytest.fixture
def promotion_10_percentage(channel_USD, product_list, product):
    promotion = Promotion.objects.create(
        name="Promotion",
    )
    product_list.append(product)
    rule = promotion.rules.create(
        name="10% promotion rule",
        catalogue_predicate={
            "productPredicate": {
                "ids": [
                    graphene.Node.to_global_id("Product", product.id)
                    for product in product_list
                ]
            }
        },
        reward_value_type=RewardValueType.PERCENTAGE,
        reward_value=Decimal("10"),
    )
    rule.channels.add(channel_USD)
    return promotion


@pytest.fixture
def promotion_converted_from_sale(catalogue_predicate, channel_USD):
    promotion = Promotion.objects.create(name="Sale", type=PromotionType.CATALOGUE)
    promotion.assign_old_sale_id()

    rule = PromotionRule.objects.create(
        name="Sale rule",
        promotion=promotion,
        catalogue_predicate=catalogue_predicate,
        reward_value_type=RewardValueType.FIXED,
        reward_value=Decimal(5),
        old_channel_listing_id=PromotionRule.get_old_channel_listing_ids(1)[0][0],
    )
    rule.channels.add(channel_USD)
    fetch_variants_for_promotion_rules(promotion.rules.all())
    return promotion


@pytest.fixture
def promotion_converted_from_sale_with_many_channels(
    promotion_converted_from_sale, catalogue_predicate, channel_PLN
):
    promotion = promotion_converted_from_sale
    rule = PromotionRule.objects.create(
        name="Sale rule 2",
        promotion=promotion,
        catalogue_predicate=catalogue_predicate,
        reward_value_type=RewardValueType.FIXED,
        reward_value=Decimal(5),
        old_channel_listing_id=PromotionRule.get_old_channel_listing_ids(1)[0][0],
    )
    rule.channels.add(channel_PLN)
    fetch_variants_for_promotion_rules(promotion.rules.all())
    return promotion


@pytest.fixture
def promotion_converted_from_sale_with_empty_predicate(channel_USD):
    promotion = Promotion.objects.create(
        name="Sale with empty predicate", type=PromotionType.CATALOGUE
    )
    promotion.assign_old_sale_id()
    rule = PromotionRule.objects.create(
        name="Sale with empty predicate rule",
        promotion=promotion,
        catalogue_predicate={},
        reward_value_type=RewardValueType.FIXED,
        reward_value=Decimal(5),
        old_channel_listing_id=PromotionRule.get_old_channel_listing_ids(1)[0][0],
    )
    rule.channels.add(channel_USD)
    return promotion


@pytest.fixture
def promotion_converted_from_sale_list(channel_USD, product_list, category, collection):
    promotions = Promotion.objects.bulk_create(
        [Promotion(name="Sale 1"), Promotion(name="Sale 2"), Promotion(name="Sale 3")]
    )
    for promotion in promotions:
        promotion.assign_old_sale_id()
    predicates = [
        {
            "OR": [
                {
                    "productPredicate": {
                        "ids": [graphene.Node.to_global_id("Product", product.id)]
                    }
                },
                {
                    "variantPredicate": {
                        "ids": [
                            graphene.Node.to_global_id(
                                "Product", product.variants.first().id
                            )
                        ]
                    }
                },
            ]
        }
        for product in product_list
    ]
    collection_id = graphene.Node.to_global_id("Collection", collection.id)
    category_id = graphene.Node.to_global_id("Category", category.id)

    predicates[0]["OR"].append({"categoryPredicate": {"ids": [category_id]}})
    predicates[1]["OR"].append({"collectionPredicate": {"ids": [collection_id]}})

    rules = [
        PromotionRule(
            promotion=promotion,
            catalogue_predicate=predicate,
            reward_value_type=RewardValueType.FIXED,
            reward_value=Decimal("5"),
        )
        for promotion, predicate in zip(promotions, predicates)
    ]
    PromotionRule.objects.bulk_create(rules)
    for rule in rules:
        rule.channels.add(channel_USD)

    return promotions
