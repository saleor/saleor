from ...utils import fetch_promotion_rules_for_order


def test_fetch_promotion_rules_for_order(order, checkout_and_order_promotion_rule):
    # given
    rule = checkout_and_order_promotion_rule

    order.total_gross_amount = 100
    order.save(update_fields=["total_gross_amount"])

    # when
    rules_per_promotion_id = fetch_promotion_rules_for_order(order)

    # then
    assert len(rules_per_promotion_id) == 1
    assert rules_per_promotion_id[rule.promotion_id] == [rule]


def test_fetch_promotion_rules_for_order_no_matching_rule(
    order, checkout_and_order_promotion_rule
):
    # given
    rule = checkout_and_order_promotion_rule

    order.total_gross_amount = 10
    order.save(update_fields=["total_gross_amount"])

    # when
    rules_per_promotion_id = fetch_promotion_rules_for_order(order)

    # then
    assert len(rules_per_promotion_id) == 0
    assert not rules_per_promotion_id[rule.promotion_id]
