from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import patch

import graphene
import pytz

from ... import RewardValueType
from ...models import Promotion, PromotionRule
from ...utils.promotion import mark_catalogue_promotion_rules_as_dirty


@patch("saleor.discount.utils.promotion.PromotionRule.objects.filter")
def test_mark_catalogue_promotion_rules_as_dirty_with_empty_list_as_input(
    mocked_promotion_rule_filter,
):
    # when
    mark_catalogue_promotion_rules_as_dirty([])

    # then
    assert not mocked_promotion_rule_filter.called


def test_mark_catalogue_promotion_rules_as_dirty_single_promotion(
    catalogue_promotion, product
):
    # given
    promotion = catalogue_promotion
    second_promotion = Promotion.objects.create(
        name="Promotion",
        end_date=datetime.now(tz=pytz.UTC) + timedelta(days=30),
    )
    PromotionRule.objects.create(
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

    rule = promotion.rules.first()
    rule.variants_dirty = False
    rule.save(update_fields=["variants_dirty"])

    # when
    mark_catalogue_promotion_rules_as_dirty([promotion])

    # then
    assert not PromotionRule.objects.filter(
        promotion_id=promotion.id, variants_dirty=False
    )
    assert not PromotionRule.objects.filter(
        promotion_id=second_promotion.id, variants_dirty=True
    )


def test_mark_catalogue_promotion_rules_as_dirty_multiple_promotion(
    catalogue_promotion, product
):
    # given
    promotion = catalogue_promotion
    second_promotion = Promotion.objects.create(
        name="Promotion",
        end_date=datetime.now(tz=pytz.UTC) + timedelta(days=30),
    )
    PromotionRule.objects.create(
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

    rule = promotion.rules.first()
    rule.variants_dirty = False
    rule.save(update_fields=["variants_dirty"])

    # when
    mark_catalogue_promotion_rules_as_dirty([promotion, second_promotion])

    # then
    assert not PromotionRule.objects.filter(
        promotion_id__in=[promotion.id, second_promotion.id], variants_dirty=False
    )
