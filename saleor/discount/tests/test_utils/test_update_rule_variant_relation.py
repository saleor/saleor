from decimal import Decimal

import graphene

from ... import RewardValueType
from ...models import PromotionRule
from ...utils.promotion import update_rule_variant_relation


def test_update_rule_variant_relation(
    catalogue_promotion_without_rules, channel_USD, product_variant_list
):
    # given
    promotion = catalogue_promotion_without_rules
    variants = product_variant_list
    PromotionRuleVariant = PromotionRule.variants.through

    for i in range(len(variants)):
        existing_variants = variants[:i]
        new_variants = variants[-i:]
        new_variant_global_ids = [
            graphene.Node.to_global_id("ProductVariant", variant.id)
            for variant in new_variants
        ]
        new_variant_ids = [variant.id for variant in new_variants]

        percentage_reward_value = Decimal("10")
        rule = promotion.rules.create(
            name="Percentage promotion rule",
            catalogue_predicate={"variantPredicate": {"ids": new_variant_global_ids}},
            reward_value_type=RewardValueType.PERCENTAGE,
            reward_value=percentage_reward_value,
        )

        rule.channels.add(channel_USD)
        rule.variants.add(*existing_variants)

        rules = PromotionRule.objects.filter(id=rule.id)
        new_variants_rules = [
            PromotionRuleVariant(promotionrule_id=rule.id, productvariant_id=variant.id)
            for variant in new_variants
        ]

        # when
        update_rule_variant_relation(rules, new_variants_rules)

        # then
        related_variants = PromotionRuleVariant.objects.filter(
            promotionrule_id=rule.id
        ).values_list("productvariant_id", flat=True)
        assert all([variant in new_variant_ids for variant in related_variants])
        assert len(related_variants) == len(new_variants)
