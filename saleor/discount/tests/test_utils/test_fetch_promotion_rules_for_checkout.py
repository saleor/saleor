from decimal import Decimal

from ... import RewardType, RewardValueType
from ...models import PromotionRule
from ...utils.promotion import fetch_promotion_rules_for_checkout_or_order


def test_fetch_promotion_rules_for_checkout(
    checkout, checkout_for_cc, order_promotion_rule
):
    # given
    rule = order_promotion_rule

    checkout.base_total_amount = 100
    checkout.base_subtotal_amount = 100
    checkout.total_gross_amount = 100
    checkout.save(
        update_fields=[
            "total_gross_amount",
            "base_total_amount",
            "base_subtotal_amount",
        ]
    )

    # when
    rules_per_promotion_id = fetch_promotion_rules_for_checkout_or_order(checkout)

    # then
    assert len(rules_per_promotion_id) == 1
    assert rules_per_promotion_id == [rule]


def test_fetch_promotion_rules_for_checkout_no_matching_rule(
    checkout,
    checkout_JPY,
    order_promotion_rule,
):
    # given
    checkout.base_total_amount = 10
    checkout.base_subtotal_amount = 10
    checkout.total_gross_amount = 10
    checkout.save(
        update_fields=[
            "total_gross_amount",
            "base_total_amount",
            "base_subtotal_amount",
        ]
    )

    # when
    rules_per_promotion_id = fetch_promotion_rules_for_checkout_or_order(checkout)

    # then
    assert not rules_per_promotion_id


def test_fetch_promotion_rules_for_checkout_relevant_channel_only(
    checkout_JPY, order_promotion_rule
):
    # given
    promotion = order_promotion_rule.promotion
    order_predicate = {
        "discountedObjectPredicate": {"baseSubtotalPrice": {"range": {"gte": 0}}}
    }
    rule_1 = order_promotion_rule
    rule_1.order_predicate = order_predicate
    rule_1.save(update_fields=["order_predicate"])

    rule_2 = PromotionRule.objects.create(
        name="Another promotion rule",
        promotion=promotion,
        order_predicate=order_predicate,
        reward_value_type=RewardValueType.PERCENTAGE,
        reward_value=Decimal("10"),
        reward_type=RewardType.SUBTOTAL_DISCOUNT,
    )
    rule_2.channels.add(checkout_JPY.channel)

    # when
    rules_per_promotion_id = fetch_promotion_rules_for_checkout_or_order(checkout_JPY)

    # then
    assert len(rules_per_promotion_id) == 1
    assert rules_per_promotion_id == [rule_2]


def test_fetch_promotion_rules_for_checkout_inner_or_operator(
    checkout, checkout_for_cc, order_promotion_rule
):
    # given
    rule = order_promotion_rule
    rule.order_predicate = {
        "discountedObjectPredicate": {
            "OR": [
                {"baseTotalPrice": {"range": {"gte": "10"}}},
                {"baseSubtotalPrice": {"range": {"gte": "10"}}},
            ]
        }
    }
    rule.save(update_fields=["order_predicate"])

    checkout.base_total_amount = 100
    checkout.base_subtotal_amount = 100
    checkout.total_gross_amount = 100
    checkout.save(
        update_fields=[
            "total_gross_amount",
            "base_total_amount",
            "base_subtotal_amount",
        ]
    )

    # when
    rules_per_promotion_id = fetch_promotion_rules_for_checkout_or_order(checkout)

    # then
    assert len(rules_per_promotion_id) == 1
    assert rules_per_promotion_id == [rule]
