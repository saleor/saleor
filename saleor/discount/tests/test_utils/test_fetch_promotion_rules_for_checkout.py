from ...utils import fetch_promotion_rules_for_checkout


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
    rules_per_promotion_id = fetch_promotion_rules_for_checkout(checkout)

    # then
    assert len(rules_per_promotion_id) == 1
    assert rules_per_promotion_id == [rule]


def test_fetch_promotion_rules_for_checkout_no_matching_rule(
    checkout, checkout_for_cc, order_promotion_rule
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
    rules_per_promotion_id = fetch_promotion_rules_for_checkout(checkout)

    # then
    assert not rules_per_promotion_id
