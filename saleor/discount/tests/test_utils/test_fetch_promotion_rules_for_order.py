from decimal import Decimal

from ... import RewardType, RewardValueType
from ...models import PromotionRule
from ...utils.promotion import fetch_promotion_rules_for_checkout_or_order


def test_fetch_promotion_rules_for_order(order, order_line_JPY, order_promotion_rule):
    # given
    rule = order_promotion_rule

    order.subtotal_net_amount = 100
    order.total_net_amount = 100
    order.save(update_fields=["subtotal_net_amount", "total_net_amount"])

    # when
    rules_per_promotion_id = fetch_promotion_rules_for_checkout_or_order(order)

    # then
    assert len(rules_per_promotion_id) == 1
    assert rules_per_promotion_id == [rule]


def test_fetch_promotion_rules_for_order_no_matching_rule(
    order,
    order_line_JPY,
    order_promotion_rule,
):
    # given
    order.subtotal_net_amount = 10
    order.total_net_amount = 10
    order.save(update_fields=["subtotal_net_amount", "total_net_amount"])

    # when
    rules_per_promotion_id = fetch_promotion_rules_for_checkout_or_order(order)

    # then
    assert not rules_per_promotion_id


def test_fetch_promotion_rules_for_order_relevant_channel_only(
    order, order_line_JPY, order_promotion_rule
):
    # given
    order_JPY = order_line_JPY.order
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
    rule_2.channels.add(order_JPY.channel)

    # when
    rules_per_promotion_id = fetch_promotion_rules_for_checkout_or_order(order_JPY)

    # then
    assert len(rules_per_promotion_id) == 1
    assert rules_per_promotion_id == [rule_2]


def test_fetch_promotion_rules_for_checkout_inner_or_operator(
    order, order_line_JPY, order_promotion_rule
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

    order.subtotal_net_amount = 100
    order.total_net_amount = 100
    order.save(update_fields=["subtotal_net_amount", "total_net_amount"])

    # when
    rules_per_promotion_id = fetch_promotion_rules_for_checkout_or_order(order)

    # then
    assert len(rules_per_promotion_id) == 1
    assert rules_per_promotion_id == [rule]
