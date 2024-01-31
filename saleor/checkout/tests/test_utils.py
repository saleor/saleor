from decimal import Decimal

import pytest
from prices import Money, TaxedMoney

from ...tax.calculations import get_taxed_undiscounted_price
from ..utils import apply_gift_reward_if_applicable

BASE = Money("35.00", "USD")


@pytest.mark.parametrize(
    ("price", "tax_rate", "prices_entered_with_tax", "result"),
    [
        # result should not be calculated but taken from price
        (
            TaxedMoney(gross=Money("43.74", "USD"), net=BASE),
            Decimal(0.25),
            False,
            TaxedMoney(gross=Money("43.74", "USD"), net=BASE),
        ),
        # result should be calculated and different from price
        (
            TaxedMoney(gross=Money("43.74", "USD"), net=Money("36.00", "USD")),
            Decimal(0.25),
            False,
            TaxedMoney(gross=Money("43.75", "USD"), net=BASE),
        ),
        # result should not be calculated and taken from price
        (
            TaxedMoney(gross=BASE, net=Money("26.26", "USD")),
            Decimal(0.25),
            True,
            TaxedMoney(gross=BASE, net=Money("26.26", "USD")),
        ),
        # result should be calculated and different from price
        (
            TaxedMoney(gross=Money("36.00", "USD"), net=Money("26.26", "USD")),
            Decimal(0.25),
            True,
            TaxedMoney(gross=BASE, net=Money("28.00", "USD")),
        ),
    ],
)
def test_get_taxed_undiscounted_price(price, tax_rate, prices_entered_with_tax, result):
    result_price = get_taxed_undiscounted_price(
        undiscounted_base_price=BASE,
        price=price,
        tax_rate=tax_rate,
        prices_entered_with_tax=prices_entered_with_tax,
    )

    assert result_price == result


def test_apply_gift_reward_if_applicable(
    checkout_with_item, gift_promotion_rule, order_promotion_rule, promotion_rule
):
    # given
    checkout = checkout_with_item
    lines_count = checkout.lines.count()

    # when
    apply_gift_reward_if_applicable(checkout)

    # then
    checkout.refresh_from_db()
    assert checkout.lines.count() == lines_count + 1
    gift_line = checkout.lines.filter(is_gift=True).first()
    assert gift_line
    assert gift_line.discounts.count() == 1


def test_apply_gift_reward_if_applicable_no_gift_promotion_rules(
    checkout_with_item, order_promotion_rule, promotion_rule
):
    # given
    checkout = checkout_with_item
    lines_count = checkout.lines.count()

    # when
    apply_gift_reward_if_applicable(checkout)

    # then
    checkout.refresh_from_db()
    assert checkout.lines.count() == lines_count


def test_apply_gift_reward_if_applicable_no_gift_promotion_rules_for_checkout_channel(
    checkout_with_item, gift_promotion_rule, order_promotion_rule, promotion_rule
):
    # given
    checkout = checkout_with_item
    lines_count = checkout.lines.count()
    gift_promotion_rule.channels.remove(checkout.channel)

    # when
    apply_gift_reward_if_applicable(checkout)

    # then
    checkout.refresh_from_db()
    assert checkout.lines.count() == lines_count
