from decimal import Decimal

import graphene

from ... import PromotionRuleInfo, RewardValueType
from ...models import Promotion, PromotionRule
from ...utils.promotion import calculate_discounted_price_for_promotions


def test_variant_discounts_multiple_promotions(product, channel_USD):
    # given
    variant = product.variants.get()

    promotion_low_discount, promotion_high_discount = Promotion.objects.bulk_create(
        [
            Promotion(
                name="Promotion 1",
            ),
            Promotion(
                name="Promotion 2",
            ),
        ]
    )

    rule_low, rule_high = PromotionRule.objects.bulk_create(
        [
            PromotionRule(
                name="Promotion 1 percentage rule",
                promotion=promotion_low_discount,
                catalogue_predicate={
                    "productPredicate": {
                        "ids": [graphene.Node.to_global_id("Product", product.id)]
                    }
                },
                reward_value_type=RewardValueType.PERCENTAGE,
                reward_value=Decimal("10"),
            ),
            PromotionRule(
                name="Promotion 2 percentage rule",
                promotion=promotion_high_discount,
                catalogue_predicate={
                    "productPredicate": {
                        "ids": [graphene.Node.to_global_id("Product", product.id)]
                    }
                },
                reward_value_type=RewardValueType.PERCENTAGE,
                reward_value=Decimal("50"),
            ),
        ]
    )
    rule_low.channels.add(channel_USD)
    rule_high.channels.add(channel_USD)

    rules_info_per_promotion_id = {
        variant.id: [
            PromotionRuleInfo(
                rule=rule_low,
                channel_ids=[channel_USD.id],
            ),
            PromotionRuleInfo(
                rule=rule_high,
                channel_ids=[channel_USD.id],
            ),
        ],
    }

    variant_channel_listing = variant.channel_listings.get(channel=channel_USD)
    price = variant_channel_listing.price

    # when
    applied_rule_id, applied_discount = calculate_discounted_price_for_promotions(
        price=price,
        rules_info_per_variant=rules_info_per_promotion_id,
        channel=channel_USD,
        variant_id=variant.id,
    )

    # then
    assert applied_rule_id == rule_high.id
    assert applied_discount == (price - rule_high.reward_value / 100 * price)


def test_variant_discounts_multiple_promotions_and_rules(product, channel_USD):
    # given
    variant = product.variants.get()

    promotion_low_discount, promotion_high_discount = Promotion.objects.bulk_create(
        [
            Promotion(
                name="Promotion 1",
            ),
            Promotion(
                name="Promotion 2",
            ),
        ]
    )

    rule_low_1, rule_low_2, rule_high_1 = PromotionRule.objects.bulk_create(
        [
            PromotionRule(
                name="Promotion rule 1",
                promotion=promotion_low_discount,
                catalogue_predicate={
                    "productPredicate": {
                        "ids": [graphene.Node.to_global_id("Product", product.id)]
                    }
                },
                reward_value_type=RewardValueType.FIXED,
                reward_value=Decimal("1"),
            ),
            PromotionRule(
                name="Promotion rule 2",
                promotion=promotion_low_discount,
                catalogue_predicate={
                    "productPredicate": {
                        "ids": [graphene.Node.to_global_id("Product", product.id)]
                    }
                },
                reward_value_type=RewardValueType.PERCENTAGE,
                reward_value=Decimal("5"),
            ),
            PromotionRule(
                name="Promotion rule 4",
                promotion=promotion_high_discount,
                catalogue_predicate={
                    "productPredicate": {
                        "ids": [graphene.Node.to_global_id("Product", product.id)]
                    }
                },
                reward_value_type=RewardValueType.PERCENTAGE,
                reward_value=Decimal("50"),
            ),
        ]
    )

    channel_USD.promotionrule_set.add(rule_low_1, rule_low_2, rule_high_1)

    rules_info_per_promotion_id = {
        variant.id: [
            PromotionRuleInfo(
                rule=rule_low_1,
                channel_ids=[channel_USD.id],
            ),
            PromotionRuleInfo(
                rule=rule_low_2,
                channel_ids=[channel_USD.id],
            ),
            PromotionRuleInfo(
                rule=rule_high_1,
                channel_ids=[channel_USD.id],
            ),
        ],
    }

    variant_channel_listing = variant.channel_listings.get(channel=channel_USD)
    price = variant_channel_listing.price

    # when
    applied_rule_id, applied_discount = calculate_discounted_price_for_promotions(
        price=price,
        rules_info_per_variant=rules_info_per_promotion_id,
        channel=channel_USD,
        variant_id=variant.id,
    )

    # then
    assert applied_rule_id == rule_high_1.id
    assert applied_discount == (price - rule_high_1.reward_value / 100 * price)
