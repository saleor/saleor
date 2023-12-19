from decimal import Decimal

import graphene

from ...discount import RewardValueType
from ...discount.models import PromotionRule
from ..utils.variants import fetch_variants_for_promotion_rules


def test_fetch_variants_for_promotion_rules_discount(
    promotion_without_rules, product, product_with_two_variants, channel_USD
):
    # given
    variant = product.variants.first()
    promotion = promotion_without_rules

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

    # when
    fetch_variants_for_promotion_rules(PromotionRule.objects.all())

    # then
    rule_1.refresh_from_db()
    assert rule_1.variants.count() == 1
    assert rule_1.variants.first() == variant

    rule_2.refresh_from_db()
    assert rule_2.variants.count() == product_with_two_variants.variants.count()
    assert list(rule_2.variants.values_list("id", flat=True)) == list(
        product_with_two_variants.variants.values_list("id", flat=True)
    )


def test_fetch_variants_for_promotion_rules_no_applicable_variants(
    promotion_without_rules, category, channel_USD
):
    # given
    category.products.clear()

    reward_value = Decimal("2")
    rule = promotion_without_rules.rules.create(
        name="Percentage promotion rule",
        catalogue_predicate={
            "categoryPredicate": {
                "ids": [graphene.Node.to_global_id("Category", category.id)]
            }
        },
        reward_value_type=RewardValueType.FIXED,
        reward_value=reward_value,
    )
    rule.channels.add(channel_USD)

    # when
    fetch_variants_for_promotion_rules(PromotionRule.objects.all())

    # then
    rule.refresh_from_db()
    assert rule.variants.count() == 0


def test_fetch_variants_for_promotion_rules_relation_already_exist(
    promotion,
):
    # given
    PromotionRuleVariant = PromotionRule.variants.through
    rule = PromotionRuleVariant.objects.first().promotionrule
    assert rule.variants.count() > 0

    # when
    fetch_variants_for_promotion_rules(PromotionRule.objects.all())

    # then
    rule.refresh_from_db()
    assert rule.variants.count() > 0
