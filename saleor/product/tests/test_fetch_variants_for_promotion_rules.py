from decimal import Decimal

import before_after
import graphene

from ...discount import RewardValueType
from ...discount.models import PromotionRule
from ...discount.utils.promotion import update_rule_variant_relation
from ..utils.variants import fetch_variants_for_promotion_rules


def test_fetch_variants_for_promotion_rules_discount(
    catalogue_promotion_without_rules,
    product,
    product_with_two_variants,
    channel_USD,
    product_variant_list,
):
    # given
    variant = product.variants.first()
    promotion = catalogue_promotion_without_rules

    percentage_reward_value = Decimal("10")
    reward_value = Decimal("2")
    rule_1 = promotion.rules.create(
        name="Percentage promotion rule",
        catalogue_predicate={
            "variantPredicate": {
                "ids": [
                    graphene.Node.to_global_id("ProductVariant", variant.id),
                    graphene.Node.to_global_id(
                        "ProductVariant", product_variant_list[0].id
                    ),
                ]
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

    # Variants not present in rules predicate should be deleted
    rule_1.variants.add(*product_variant_list)
    rule_2.variants.add(*product_variant_list)

    # when
    fetch_variants_for_promotion_rules(PromotionRule.objects.all())

    # then
    rule_1.refresh_from_db()
    rule_1_variants = rule_1.variants.all()
    assert len(rule_1_variants) == 2
    assert variant in rule_1_variants
    assert product_variant_list[0] in rule_1_variants

    rule_2.refresh_from_db()
    assert rule_2.variants.count() == product_with_two_variants.variants.count()
    assert list(rule_2.variants.values_list("id", flat=True)) == list(
        product_with_two_variants.variants.values_list("id", flat=True)
    )


def test_fetch_variants_for_promotion_rules_empty_catalogue_predicate(
    catalogue_promotion_without_rules, product, product_with_two_variants, channel_USD
):
    # given
    promotion = catalogue_promotion_without_rules

    percentage_reward_value = Decimal("10")
    rule_1 = promotion.rules.create(
        name="Percentage promotion rule",
        catalogue_predicate={},
        reward_value_type=RewardValueType.PERCENTAGE,
        reward_value=percentage_reward_value,
    )
    rule_1.channels.add(channel_USD)

    # when
    fetch_variants_for_promotion_rules(PromotionRule.objects.all())

    # then
    rule_1.refresh_from_db()
    assert rule_1.variants.count() == 0


def test_fetch_variants_for_promotion_rules_no_applicable_variants(
    catalogue_promotion_without_rules, category, channel_USD
):
    # given
    category.products.clear()

    reward_value = Decimal("2")
    rule = catalogue_promotion_without_rules.rules.create(
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
    catalogue_promotion,
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


def test_fetch_variants_for_promotion_rules_discount_race_condition(
    catalogue_promotion_without_rules,
    channel_USD,
    product_variant_list,
):
    # given
    promotion = catalogue_promotion_without_rules
    existing_variant = product_variant_list[0]
    new_variant = product_variant_list[1]

    percentage_reward_value = Decimal("10")
    rule = promotion.rules.create(
        name="Percentage promotion rule",
        catalogue_predicate={
            "variantPredicate": {
                "ids": [
                    graphene.Node.to_global_id("ProductVariant", new_variant.id),
                ]
            }
        },
        reward_value_type=RewardValueType.PERCENTAGE,
        reward_value=percentage_reward_value,
    )
    rule.channels.add(channel_USD)
    rule.variants.add(existing_variant)

    # when
    with before_after.after(
        "saleor.product.utils.variants.update_rule_variant_relation",
        update_rule_variant_relation,
    ):
        fetch_variants_for_promotion_rules(PromotionRule.objects.all())

    # then
    rule.refresh_from_db()
    rule_variants = rule.variants.all()
    assert len(rule_variants) == 1
    assert new_variant in rule_variants
