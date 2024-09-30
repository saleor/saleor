from decimal import Decimal

import graphene
import pytest
from prices import Money, TaxedMoney

from ...discount import DiscountType, DiscountValueType
from ...tax.calculations import get_taxed_undiscounted_price
from ..utils import checkout_info_for_logs

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


def test_checkout_info_for_logs(checkout_info, voucher, order_promotion_with_rule):
    # given
    checkout = checkout_info.checkout
    voucher_code = voucher.codes.first().code
    checkout.voucher_code = voucher_code

    checkout_discount = checkout.discounts.create(
        type=DiscountType.ORDER_PROMOTION,
        value_type=DiscountValueType.FIXED,
        value=Decimal(5),
        amount_value=Decimal(5),
        promotion_rule=order_promotion_with_rule.rules.first(),
        currency=checkout.currency,
    )
    checkout_info.discounts = [checkout_discount]

    lines_info = checkout_info.lines
    line_discount = lines_info[0].line.discounts.create(
        type=DiscountType.VOUCHER,
        value_type=DiscountValueType.FIXED,
        value=Decimal(5),
        currency=checkout.currency,
        amount_value=Decimal(5),
        voucher=voucher,
    )
    lines_info[0].discounts = [line_discount]

    # when
    extra = checkout_info_for_logs(checkout_info, lines_info)

    # then
    assert extra["checkout_id"] == graphene.Node.to_global_id("Checkout", checkout.pk)
    assert extra["discounts"]
    assert extra["lines"][0]["discounts"]
