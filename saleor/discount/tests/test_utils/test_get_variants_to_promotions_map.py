from decimal import Decimal

import graphene

from ....product.models import ProductVariant
from ....product.utils.variants import fetch_variants_for_promotion_rules
from ... import PromotionRuleInfo, RewardValueType
from ...models import Promotion, PromotionRule
from ...utils.promotion import get_variants_to_promotion_rules_map


def test_get_variants_to_promotions_map(
    catalogue_promotion_without_rules, product, product_with_two_variants, channel_USD
):
    # given
    promotion = catalogue_promotion_without_rules
    variant = product.variants.first()

    percentage_reward_value = Decimal("10")
    reward_value = Decimal("2")
    rule_1 = promotion.rules.create(
        name="Percentage promotion rule",
        catalogue_predicate={
            "variantPredicate": {
                "ids": [graphene.Node.to_global_id("ProductVariant", variant.id)]
            }
        },
        reward_value_type=RewardValueType.PERCENTAGE,
        reward_value=percentage_reward_value,
    )
    rule_2 = promotion.rules.create(
        name="Fixed promotion rule",
        catalogue_predicate={
            "productPredicate": {
                "ids": [
                    graphene.Node.to_global_id("Product", product_with_two_variants.id)
                ]
            }
        },
        reward_value_type=RewardValueType.FIXED,
        reward_value=reward_value,
    )
    rule_1.channels.add(channel_USD)
    rule_2.channels.add(channel_USD)
    rule_1.variants.add(variant)
    rule_2.variants.set(product_with_two_variants.variants.all())

    variants = ProductVariant.objects.all()

    # when
    rules_info_per_variant = get_variants_to_promotion_rules_map(variants)

    # then
    assert len(rules_info_per_variant) == 3
    assert rules_info_per_variant[variant.id] == [
        PromotionRuleInfo(rule=rule_1, channel_ids=[channel_USD.id]),
    ]

    for variant in product_with_two_variants.variants.all():
        assert rules_info_per_variant[variant.id] == [
            PromotionRuleInfo(rule=rule_2, channel_ids=[channel_USD.id]),
        ]


def test_get_variants_to_promotions_map_from_different_promotions(
    catalogue_promotion_without_rules, product, channel_USD
):
    # given
    promotion = catalogue_promotion_without_rules
    promotion_2 = Promotion.objects.create(
        name="Promotion",
    )
    variant = product.variants.first()

    percentage_reward_value = Decimal("10")
    reward_value = Decimal("2")
    rule_1 = promotion.rules.create(
        name="Percentage promotion rule",
        catalogue_predicate={
            "variantPredicate": {
                "ids": [graphene.Node.to_global_id("ProductVariant", variant.id)]
            }
        },
        reward_value_type=RewardValueType.PERCENTAGE,
        reward_value=percentage_reward_value,
    )
    rule_2 = promotion_2.rules.create(
        name="Fixed promotion rule",
        catalogue_predicate={
            "productPredicate": {
                "ids": [graphene.Node.to_global_id("Product", product.id)]
            }
        },
        reward_value_type=RewardValueType.FIXED,
        reward_value=reward_value,
    )
    rule_1.channels.add(channel_USD)
    rule_2.channels.add(channel_USD)
    rule_1.variants.add(variant)
    rule_2.variants.add(variant)

    variants = ProductVariant.objects.all()

    # when
    rules_info_per_variant = get_variants_to_promotion_rules_map(variants)

    # then
    assert len(rules_info_per_variant) == 1
    assert len(rules_info_per_variant[variant.id]) == 2
    expected_rules = [
        PromotionRuleInfo(rule=rule_1, channel_ids=[channel_USD.id]),
        PromotionRuleInfo(rule=rule_2, channel_ids=[channel_USD.id]),
    ]
    for rule in rules_info_per_variant[variant.id]:
        assert rule in expected_rules


def test_get_variants_to_promotions_map_no_active_rules(product):
    # given
    variants = ProductVariant.objects.all()
    fetch_variants_for_promotion_rules(PromotionRule.objects.all())

    # when
    rules_info_per_variant = get_variants_to_promotion_rules_map(variants)

    # then
    assert not rules_info_per_variant


def test_get_variants_to_promotions_map_no_matching_rules(
    product_with_two_variants, variant, catalogue_promotion_without_rules
):
    # given
    promotion = catalogue_promotion_without_rules

    percentage_reward_value = Decimal("10")
    rule = promotion.rules.create(
        name="Percentage promotion rule",
        catalogue_predicate={
            "productPredicate": {
                "ids": [
                    graphene.Node.to_global_id("Product", product_with_two_variants.id)
                ]
            }
        },
        reward_value_type=RewardValueType.PERCENTAGE,
        reward_value=percentage_reward_value,
    )
    rule.variants.set(product_with_two_variants.variants.all())

    variants = ProductVariant.objects.filter(id=variant.id)

    # when
    rules_info_per_variant = get_variants_to_promotion_rules_map(variants)

    # then
    assert not rules_info_per_variant
