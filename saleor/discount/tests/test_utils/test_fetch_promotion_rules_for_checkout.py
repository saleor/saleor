from ...utils import fetch_promotion_rules_for_checkout


def test_fetch_promotion_rules_for_checkout(
    checkout, checkout_for_cc, checkout_and_order_promotion_rule
):
    # given
    rule = checkout_and_order_promotion_rule

    checkout.total_gross_amount = 100
    checkout.save(update_fields=["total_gross_amount"])

    # when
    rules_per_promotion_id = fetch_promotion_rules_for_checkout(checkout)

    # then
    assert len(rules_per_promotion_id) == 1
    assert rules_per_promotion_id[rule.promotion_id] == [rule]


def test_fetch_promotion_rules_for_checkout_no_matching_rule(
    checkout, checkout_for_cc, checkout_and_order_promotion_rule
):
    # given
    rule = checkout_and_order_promotion_rule

    checkout.total_gross_amount = 10
    checkout.save(update_fields=["total_gross_amount"])

    # when
    rules_per_promotion_id = fetch_promotion_rules_for_checkout(checkout)

    # then
    assert len(rules_per_promotion_id) == 0
    assert not rules_per_promotion_id[rule.promotion_id]
