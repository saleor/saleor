from decimal import Decimal

import graphene
import pytest

from ....discount import RewardValueType
from ....discount.models import (
    Promotion,
    PromotionRule,
    PromotionRuleTranslation,
    PromotionTranslation,
)


@pytest.fixture
def promotion_list_for_benchmark(channel_USD, channel_PLN, product_list):
    promotions = Promotion.objects.bulk_create(
        [Promotion(name=f"Promotion-{i}") for i in range(30)]
    )
    rules = [
        PromotionRule(
            promotion=promotion,
            catalogue_predicate={},
            reward_value_type=RewardValueType.PERCENTAGE,
            reward_value=Decimal("10"),
        )
        for promotion in promotions
    ]
    for rule, product in zip(rules, product_list):
        rule.catalogue_predicate = {
            "productPredicate": {
                "ids": [graphene.Node.to_global_id("Product", product.id)]
            }
        }

    PromotionRule.objects.bulk_create(rules)

    channel_PLN.promotionrule_set.add(*rules)
    channel_USD.promotionrule_set.add(*rules)

    # TODO: add translations
    promotion_translations = []
    for promotion in promotions:
        promotion_translations.append(
            PromotionTranslation(
                language_code="pl",
                promotion=promotion,
                name="Polish promotion name",
            )
        )
    PromotionTranslation.objects.bulk_create(promotion_translations)

    promotion_rule_translations = []
    for rule in rules:
        promotion_rule_translations.append(
            PromotionRuleTranslation(
                language_code="pl",
                promotion_rule=rule,
                name="Polish promotion rule name",
            )
        )
    PromotionRuleTranslation.objects.bulk_create(promotion_rule_translations)

    return promotions


@pytest.fixture
def promotion_converted_from_sale_list_for_benchmark(channel_USD, channel_PLN):
    promotions = Promotion.objects.bulk_create(
        [Promotion(name="Sale1"), Promotion(name="Sale2"), Promotion(name="Sale2")]
    )
    for promotion in promotions:
        promotion.assign_old_sale_id()

    values = [15, 5, 25]
    usd_rules, pln_rules = [], []
    for promotion, value in zip(promotions, values):
        usd_rules.append(
            PromotionRule(
                promotion=promotion,
                catalogue_predicate={},
                reward_value_type=RewardValueType.FIXED,
                reward_value=value,
            )
        )
        pln_rules.append(
            PromotionRule(
                promotion=promotion,
                catalogue_predicate={},
                reward_value_type=RewardValueType.FIXED,
                reward_value=value * 2,
            )
        )
    PromotionRule.objects.bulk_create(usd_rules + pln_rules)
    PromotionRuleChannel = PromotionRule.channels.through
    usd_rules_channels = [
        PromotionRuleChannel(promotionrule_id=rule.id, channel_id=channel_USD.id)
        for rule in usd_rules
    ]
    pln_rules_channels = [
        PromotionRuleChannel(promotionrule_id=rule.id, channel_id=channel_PLN.id)
        for rule in usd_rules
    ]
    PromotionRuleChannel.objects.bulk_create(usd_rules_channels + pln_rules_channels)

    return promotions
