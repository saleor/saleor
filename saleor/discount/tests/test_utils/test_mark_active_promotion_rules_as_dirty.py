from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import patch

import graphene
import pytz

from ... import RewardValueType
from ...models import Promotion, PromotionRule
from ...utils.promotion import mark_active_catalogue_promotion_rules_as_dirty


@patch("saleor.discount.utils.promotion.PromotionRule.channels.through.objects.filter")
def test_mark_active_catalogue_promotion_rules_as_dirty_with_empty_channel_list(
    mocked_promotion_channel_filter,
):
    # when
    mark_active_catalogue_promotion_rules_as_dirty([])

    # then
    assert not mocked_promotion_channel_filter.called


def test_mark_active_catalogue_promotion_rules_as_dirty_with_single_channel(
    catalogue_promotion, channel_PLN
):
    # given
    rules = catalogue_promotion.rules.all()
    first_rule = rules.first()

    first_rule.channels.add(channel_PLN)
    assert rules.count() > 1

    # when
    mark_active_catalogue_promotion_rules_as_dirty([channel_PLN.id])

    # then
    first_rule.refresh_from_db()
    assert first_rule.variants_dirty
    assert rules.filter(variants_dirty=True).count() == 1


def test_mark_active_catalogue_promotion_rules_as_dirty_with_multiple_channels(
    product, catalogue_promotion, channel_PLN, channel_JPY, channel_USD
):
    # given
    second_promotion = Promotion.objects.create(
        name="Promotion",
        end_date=datetime.now(tz=pytz.UTC) + timedelta(days=30),
    )
    rule_for_second_promotion = PromotionRule.objects.create(
        name="Percentage promotion rule",
        promotion=second_promotion,
        catalogue_predicate={
            "productPredicate": {
                "ids": [graphene.Node.to_global_id("Product", product.id)]
            }
        },
        reward_value_type=RewardValueType.PERCENTAGE,
        reward_value=Decimal("10"),
        variants_dirty=False,
    )

    rule_for_second_promotion.channels.add(channel_JPY)

    rules = catalogue_promotion.rules.all()
    first_rule = rules.first()

    first_rule.channels.set([channel_PLN, channel_JPY])

    # when
    mark_active_catalogue_promotion_rules_as_dirty([channel_USD.id, channel_PLN.id])

    # then
    PromotionRuleChannel = PromotionRule.channels.through
    channel_relations = PromotionRuleChannel.objects.filter(
        channel_id__in=[channel_USD.id, channel_PLN.id]
    )
    assert (
        PromotionRule.objects.filter(
            id__in=channel_relations.values_list("promotionrule_id", flat=True),
            variants_dirty=False,
        ).count()
        == 0
    )

    rule_for_second_promotion.refresh_from_db()
    assert not rule_for_second_promotion.variants_dirty


def test_mark_active_promotion_rules_as_dirty_with_multiple_promotions_and_channels(
    product, catalogue_promotion, channel_PLN, channel_JPY, channel_USD
):
    # given
    second_promotion = Promotion.objects.create(
        name="Promotion",
        end_date=datetime.now(tz=pytz.UTC) + timedelta(days=30),
    )
    rule_for_second_promotion = PromotionRule.objects.create(
        name="Percentage promotion rule",
        promotion=second_promotion,
        catalogue_predicate={
            "productPredicate": {
                "ids": [graphene.Node.to_global_id("Product", product.id)]
            }
        },
        reward_value_type=RewardValueType.PERCENTAGE,
        reward_value=Decimal("10"),
        variants_dirty=False,
    )

    rule_for_second_promotion.channels.add(channel_PLN, channel_JPY)

    rules = catalogue_promotion.rules.all()
    first_rule = rules.first()

    first_rule.channels.set([channel_PLN, channel_JPY])

    # when
    mark_active_catalogue_promotion_rules_as_dirty([channel_USD.id, channel_PLN.id])

    # then
    PromotionRuleChannel = PromotionRule.channels.through
    channel_relations = PromotionRuleChannel.objects.filter(
        channel_id__in=[channel_USD.id, channel_PLN.id]
    )
    assert (
        PromotionRule.objects.filter(
            id__in=channel_relations.values_list("promotionrule_id", flat=True),
            variants_dirty=False,
        ).count()
        == 0
    )

    rule_for_second_promotion.refresh_from_db()
    assert rule_for_second_promotion.variants_dirty
