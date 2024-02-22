from decimal import Decimal

import pytest
from prices import Money

from ...core.prices import quantize_price
from ...core.taxes import zero_money
from ...discount import DiscountType, DiscountValueType
from ...order.base_calculations import (
    apply_order_discounts,
    apply_subtotal_discount_to_order_lines,
)


def test_apply_order_discounts_voucher_entire_order(order_with_lines, voucher):
    # given
    order = order_with_lines
    lines = order.lines.all()
    shipping_price = order.shipping_price.net
    currency = order.currency
    subtotal = zero_money(currency)
    for line in lines:
        subtotal += line.base_unit_price * line.quantity

    discount_amount = 10
    order_discount = order.discounts.create(
        type=DiscountType.VOUCHER,
        value_type=DiscountValueType.FIXED,
        value=discount_amount,
        name="Voucher",
        translated_name="VoucherPL",
        currency=currency,
        amount_value=0,
        voucher=voucher,
    )

    # when
    discounted_subtotal, discounted_shipping_price = apply_order_discounts(order, lines)

    # then
    assert discounted_shipping_price == shipping_price
    assert discounted_subtotal == subtotal - Money(discount_amount, currency)
    assert order.subtotal_net_amount == discounted_subtotal.amount
    assert order.subtotal_gross_amount == discounted_subtotal.amount
    assert order.total_net == discounted_subtotal + discounted_shipping_price
    assert order.total_gross == discounted_subtotal + discounted_shipping_price
    assert order.shipping_price_net == discounted_shipping_price
    assert order.shipping_price_gross == discounted_shipping_price
    assert order.undiscounted_total_net == subtotal + shipping_price
    assert order.undiscounted_total_gross == subtotal + shipping_price
    order_discount.refresh_from_db()
    assert order_discount.amount_value == discount_amount


def test_apply_order_discounts_voucher_entire_order_exceed_subtotal(
    order_with_lines, voucher
):
    # given
    order = order_with_lines
    lines = order.lines.all()
    shipping_price = order.shipping_price.net
    currency = order.currency
    subtotal = zero_money(currency)
    for line in lines:
        subtotal += line.base_unit_price * line.quantity

    discount_amount = 100
    assert Money(discount_amount, currency) > subtotal

    order_discount = order.discounts.create(
        type=DiscountType.VOUCHER,
        value_type=DiscountValueType.FIXED,
        value=discount_amount,
        name="Voucher",
        translated_name="VoucherPL",
        currency=currency,
        amount_value=0,
        voucher=voucher,
    )

    # when
    discounted_subtotal, discounted_shipping_price = apply_order_discounts(order, lines)

    # then
    assert discounted_shipping_price == shipping_price
    assert discounted_subtotal == zero_money(currency)
    assert order.total_net == discounted_shipping_price
    assert order.total_gross == discounted_shipping_price
    assert order.shipping_price_net == discounted_shipping_price
    assert order.shipping_price_gross == discounted_shipping_price
    assert order.undiscounted_total_net == subtotal + shipping_price
    assert order.undiscounted_total_gross == subtotal + shipping_price
    order_discount.refresh_from_db()
    assert order_discount.amount_value == subtotal.amount


def test_apply_order_discounts_voucher_entire_order_percentage(
    order_with_lines, voucher_percentage
):
    # given
    order = order_with_lines
    lines = order.lines.all()
    shipping_price = order.shipping_price.net
    currency = order.currency
    subtotal = zero_money(currency)
    for line in lines:
        subtotal += line.base_unit_price * line.quantity

    discount_amount = 50
    order_discount = order.discounts.create(
        type=DiscountType.VOUCHER,
        value_type=DiscountValueType.PERCENTAGE,
        value=discount_amount,
        name="Voucher",
        translated_name="VoucherPL",
        currency=currency,
        amount_value=0,
        voucher=voucher_percentage,
    )

    # when
    discounted_subtotal, discounted_shipping_price = apply_order_discounts(order, lines)

    # then
    assert discounted_shipping_price == shipping_price
    assert discounted_subtotal == Money(subtotal.amount / 2, currency)
    assert order.total_net == discounted_subtotal + discounted_shipping_price
    assert order.total_gross == discounted_subtotal + discounted_shipping_price
    assert order.shipping_price_net == discounted_shipping_price
    assert order.shipping_price_gross == discounted_shipping_price
    assert order.undiscounted_total_net == subtotal + shipping_price
    assert order.undiscounted_total_gross == subtotal + shipping_price
    order_discount.refresh_from_db()
    assert order_discount.amount_value == quantize_price(subtotal.amount / 2, currency)


def test_apply_order_discounts_manual_discount(order_with_lines):
    # given
    order = order_with_lines
    lines = order.lines.all()
    shipping_price = order.shipping_price.net
    currency = order.currency
    subtotal = zero_money(currency)
    for line in lines:
        subtotal += line.base_unit_price * line.quantity

    discount_amount = 8
    order_discount = order.discounts.create(
        type=DiscountType.MANUAL,
        value_type=DiscountValueType.FIXED,
        value=discount_amount,
        name="StaffDiscount",
        translated_name="StaffDiscountPL",
        currency=currency,
        amount_value=0,
    )
    undiscounted_total = subtotal + shipping_price
    shipping_share = shipping_price / undiscounted_total
    subtotal_share = 1 - shipping_share

    # when
    discounted_subtotal, discounted_shipping_price = apply_order_discounts(order, lines)

    # then
    assert discounted_shipping_price == shipping_price - shipping_share * Money(
        discount_amount, currency
    )
    assert discounted_subtotal == subtotal - subtotal_share * Money(
        discount_amount, currency
    )
    assert order.total_net == discounted_subtotal + discounted_shipping_price
    assert order.total_gross == discounted_subtotal + discounted_shipping_price
    assert order.shipping_price_net == discounted_shipping_price
    assert order.shipping_price_gross == discounted_shipping_price
    assert order.undiscounted_total_net == subtotal + shipping_price
    assert order.undiscounted_total_gross == subtotal + shipping_price
    order_discount.refresh_from_db()
    assert order_discount.amount_value == discount_amount


def test_apply_order_discounts_manual_discount_and_zero_order_total(order):
    # given
    lines = order.lines.all()
    assert not lines

    currency = order.currency
    order.discounts.create(
        type=DiscountType.MANUAL,
        value_type=DiscountValueType.FIXED,
        value=0,
        name="StaffDiscount",
        translated_name="StaffDiscountPL",
        currency=currency,
        amount_value=0,
    )

    # when
    discounted_subtotal, discounted_shipping_price = apply_order_discounts(order, lines)

    # then
    assert discounted_subtotal + discounted_shipping_price == zero_money(currency)


def test_apply_order_discounts_manual_discount_exceed_total(order_with_lines):
    # given
    order = order_with_lines
    lines = order.lines.all()
    shipping_price = order.shipping_price.net
    currency = order.currency
    subtotal = zero_money(currency)
    for line in lines:
        subtotal += line.base_unit_price * line.quantity
    undiscounted_total = subtotal + shipping_price

    discount_amount = 160
    assert Money(discount_amount, currency) > undiscounted_total
    order_discount = order.discounts.create(
        type=DiscountType.MANUAL,
        value_type=DiscountValueType.FIXED,
        value=discount_amount,
        name="StaffDiscount",
        translated_name="StaffDiscountPL",
        currency=currency,
        amount_value=0,
    )

    # when
    discounted_subtotal, discounted_shipping_price = apply_order_discounts(order, lines)

    # then
    assert discounted_shipping_price == zero_money(currency)
    assert discounted_subtotal == zero_money(currency)
    assert order.total_net == zero_money(currency)
    assert order.total_gross == zero_money(currency)
    assert order.shipping_price_net == zero_money(currency)
    assert order.shipping_price_gross == zero_money(currency)
    assert order.undiscounted_total_net == undiscounted_total
    assert order.undiscounted_total_gross == undiscounted_total
    order_discount.refresh_from_db()
    assert order_discount.amount_value == undiscounted_total.amount


def test_apply_order_discounts_manual_discount_percentage(order_with_lines):
    # given
    order = order_with_lines
    lines = order.lines.all()
    shipping_price = order.shipping_price.net
    currency = order.currency
    subtotal = zero_money(currency)
    for line in lines:
        subtotal += line.base_unit_price * line.quantity
    undiscounted_total = subtotal + shipping_price

    discount_amount = undiscounted_total.amount * Decimal(0.5)
    order_discount = order.discounts.create(
        type=DiscountType.MANUAL,
        value_type=DiscountValueType.PERCENTAGE,
        value=50,
        name="StaffDiscount",
        translated_name="StaffDiscountPL",
        currency=currency,
        amount_value=0,
    )

    # when
    discounted_subtotal, discounted_shipping_price = apply_order_discounts(order, lines)

    # then
    discounted_total = discounted_subtotal + discounted_shipping_price
    assert discounted_shipping_price == shipping_price / 2
    assert discounted_subtotal == subtotal / 2
    assert order.total_net == discounted_total
    assert order.total_gross == discounted_total
    assert order.shipping_price_net == discounted_shipping_price
    assert order.shipping_price_gross == discounted_shipping_price
    assert order.undiscounted_total_net == undiscounted_total
    assert order.undiscounted_total_gross == undiscounted_total
    order_discount.refresh_from_db()
    assert order_discount.amount_value == discount_amount


def test_apply_order_discounts_voucher_entire_order_and_manual_discount_fixed(
    order_with_lines, voucher
):
    # given
    order = order_with_lines
    lines = order.lines.all()
    shipping_price = order.shipping_price.net
    currency = order.currency
    subtotal = zero_money(currency)
    for line in lines:
        subtotal += line.base_unit_price * line.quantity
    undiscounted_total = subtotal + shipping_price
    expected_subtotal = subtotal
    expected_shipping = shipping_price

    voucher_discount_amount = 10
    voucher_order_discount = order.discounts.create(
        type=DiscountType.VOUCHER,
        value_type=DiscountValueType.FIXED,
        value=voucher_discount_amount,
        name="Voucher",
        translated_name="VoucherPL",
        currency=currency,
        amount_value=0,
        voucher=voucher,
    )
    # entire order voucher is applied to subtotal only
    expected_subtotal -= Money(voucher_discount_amount, currency)

    manual_discount_amount = 8
    manual_order_discount = order.discounts.create(
        type=DiscountType.MANUAL,
        value_type=DiscountValueType.FIXED,
        value=manual_discount_amount,
        name="StaffDiscount",
        translated_name="StaffDiscountPL",
        currency=currency,
        amount_value=0,
    )
    # manual discount is applied to both subtotal and shipping price
    subtotal_share = expected_subtotal / (expected_subtotal + expected_shipping)
    subtotal_discount = subtotal_share * manual_discount_amount
    shipping_discount = manual_discount_amount - subtotal_discount
    expected_subtotal -= Money(subtotal_discount, currency)
    expected_shipping -= Money(shipping_discount, currency)

    # when
    discounted_subtotal, discounted_shipping_price = apply_order_discounts(order, lines)

    # then
    assert discounted_shipping_price == expected_shipping
    assert discounted_subtotal == expected_subtotal
    assert order.total_net == expected_shipping + expected_subtotal
    assert order.total_gross == expected_shipping + expected_subtotal
    assert order.shipping_price_net == discounted_shipping_price
    assert order.shipping_price_gross == discounted_shipping_price
    assert order.undiscounted_total_net == undiscounted_total
    assert order.undiscounted_total_gross == undiscounted_total
    voucher_order_discount.refresh_from_db()
    assert voucher_order_discount.amount_value == voucher_discount_amount
    manual_order_discount.refresh_from_db()
    assert manual_order_discount.amount_value == manual_discount_amount


def test_apply_order_discounts_manual_discount_fixed_and_voucher_entire_order(
    order_with_lines, voucher
):
    # given
    order = order_with_lines
    lines = order.lines.all()
    shipping_price = order.shipping_price.net
    currency = order.currency
    subtotal = zero_money(currency)
    for line in lines:
        subtotal += line.base_unit_price * line.quantity
    undiscounted_total = subtotal + shipping_price
    expected_subtotal = subtotal
    expected_shipping = shipping_price
    subtotal_share = subtotal / undiscounted_total

    manual_discount_amount = 8
    manual_order_discount = order.discounts.create(
        type=DiscountType.MANUAL,
        value_type=DiscountValueType.FIXED,
        value=manual_discount_amount,
        name="StaffDiscount",
        translated_name="StaffDiscountPL",
        currency=currency,
        amount_value=0,
    )
    # manual discount is applied to both subtotal and shipping price
    subtotal_discount = subtotal_share * manual_discount_amount
    shipping_discount = manual_discount_amount - subtotal_discount
    expected_subtotal -= Money(subtotal_discount, currency)
    expected_shipping -= Money(shipping_discount, currency)

    voucher_discount_amount = 10
    voucher_order_discount = order.discounts.create(
        type=DiscountType.VOUCHER,
        value_type=DiscountValueType.FIXED,
        value=voucher_discount_amount,
        name="Voucher",
        translated_name="VoucherPL",
        currency=currency,
        amount_value=0,
        voucher=voucher,
    )
    # entire order voucher is applied to subtotal only
    expected_subtotal -= Money(voucher_discount_amount, currency)

    # when
    discounted_subtotal, discounted_shipping_price = apply_order_discounts(order, lines)

    # then
    assert discounted_shipping_price == expected_shipping
    assert discounted_subtotal == expected_subtotal
    assert order.total_net == expected_shipping + expected_subtotal
    assert order.total_gross == expected_shipping + expected_subtotal
    assert order.shipping_price_net == discounted_shipping_price
    assert order.shipping_price_gross == discounted_shipping_price
    assert order.undiscounted_total_net == undiscounted_total
    assert order.undiscounted_total_gross == undiscounted_total
    voucher_order_discount.refresh_from_db()
    assert voucher_order_discount.amount_value == voucher_discount_amount
    manual_order_discount.refresh_from_db()
    assert manual_order_discount.amount_value == manual_discount_amount


def test_apply_order_discounts_voucher_entire_order_and_manual_discount_percentage(
    order_with_lines,
    voucher_percentage,
):
    # given
    order = order_with_lines
    lines = order.lines.all()
    shipping_price = order.shipping_price.net
    currency = order.currency
    subtotal = zero_money(currency)
    for line in lines:
        subtotal += line.base_unit_price * line.quantity
    undiscounted_total = subtotal + shipping_price
    expected_subtotal = subtotal
    expected_shipping = shipping_price

    voucher_value = 50
    voucher_order_discount = order.discounts.create(
        type=DiscountType.VOUCHER,
        value_type=DiscountValueType.PERCENTAGE,
        value=voucher_value,
        name="Voucher",
        translated_name="VoucherPL",
        currency=currency,
        amount_value=0,
        voucher=voucher_percentage,
    )
    # entire order voucher is applied to subtotal only
    voucher_discount = Decimal(voucher_value / 100) * expected_subtotal
    expected_subtotal -= voucher_discount

    manual_discount_value = 50
    manual_order_discount = order.discounts.create(
        type=DiscountType.MANUAL,
        value_type=DiscountValueType.PERCENTAGE,
        value=manual_discount_value,
        name="StaffDiscount",
        translated_name="StaffDiscountPL",
        currency=currency,
        amount_value=0,
    )
    # manual discount is applied to both subtotal and shipping price
    manual_discount_subtotal = Decimal(manual_discount_value / 100) * expected_subtotal
    expected_subtotal -= manual_discount_subtotal
    manual_discount_shipping = Decimal(manual_discount_value / 100) * expected_shipping
    expected_shipping -= manual_discount_shipping
    manual_discount = manual_discount_subtotal + manual_discount_shipping

    # when
    discounted_subtotal, discounted_shipping_price = apply_order_discounts(order, lines)

    # then
    assert discounted_shipping_price == expected_shipping
    assert discounted_subtotal == expected_subtotal
    assert order.total_net == expected_shipping + expected_subtotal
    assert order.total_gross == expected_shipping + expected_subtotal
    assert order.shipping_price_net == discounted_shipping_price
    assert order.shipping_price_gross == discounted_shipping_price
    assert order.undiscounted_total_net == undiscounted_total
    assert order.undiscounted_total_gross == undiscounted_total
    voucher_order_discount.refresh_from_db()
    assert voucher_order_discount.amount_value == voucher_discount.amount
    manual_order_discount.refresh_from_db()
    assert manual_order_discount.amount_value == manual_discount.amount


def test_apply_order_discounts_manual_discount_percentage_and_voucher_entire_order(
    order_with_lines,
    voucher_percentage,
):
    # given
    order = order_with_lines
    lines = order.lines.all()
    shipping_price = order.shipping_price.net
    currency = order.currency
    subtotal = zero_money(currency)
    for line in lines:
        subtotal += line.base_unit_price * line.quantity
    undiscounted_total = subtotal + shipping_price
    expected_subtotal = subtotal
    expected_shipping = shipping_price

    manual_discount_value = 50
    manual_order_discount = order.discounts.create(
        type=DiscountType.MANUAL,
        value_type=DiscountValueType.PERCENTAGE,
        value=manual_discount_value,
        name="StaffDiscount",
        translated_name="StaffDiscountPL",
        currency=currency,
        amount_value=0,
    )
    # manual discount is applied to both subtotal and shipping price
    manual_discount_subtotal = Decimal(manual_discount_value / 100) * expected_subtotal
    expected_subtotal -= manual_discount_subtotal
    manual_discount_shipping = Decimal(manual_discount_value / 100) * expected_shipping
    expected_shipping -= manual_discount_shipping
    manual_discount = manual_discount_subtotal + manual_discount_shipping

    voucher_value = 50
    voucher_order_discount = order.discounts.create(
        type=DiscountType.VOUCHER,
        value_type=DiscountValueType.PERCENTAGE,
        value=voucher_value,
        name="Voucher",
        translated_name="VoucherPL",
        currency=currency,
        amount_value=0,
        voucher=voucher_percentage,
    )
    # entire order voucher is applied to subtotal only
    voucher_discount = Decimal(voucher_value / 100) * expected_subtotal
    expected_subtotal -= voucher_discount

    # when
    discounted_subtotal, discounted_shipping_price = apply_order_discounts(order, lines)

    # then
    assert discounted_shipping_price == expected_shipping
    assert discounted_subtotal == expected_subtotal
    assert order.total_net == expected_shipping + expected_subtotal
    assert order.total_gross == expected_shipping + expected_subtotal
    assert order.shipping_price_net == discounted_shipping_price
    assert order.shipping_price_gross == discounted_shipping_price
    assert order.undiscounted_total_net == undiscounted_total
    assert order.undiscounted_total_gross == undiscounted_total
    voucher_order_discount.refresh_from_db()
    assert voucher_order_discount.amount_value == voucher_discount.amount
    manual_order_discount.refresh_from_db()
    assert manual_order_discount.amount_value == manual_discount.amount


@pytest.mark.parametrize("discount", ["10", "1", "17.3", "10000", "0"])
def test_apply_subtotal_discount_to_order_lines(
    discount,
    order_with_lines,
    voucher,
):
    # given
    order = order_with_lines
    currency = order.currency

    def _quantize(price):
        return quantize_price(price, currency)

    lines = order.lines.all()
    subtotal = zero_money(currency)
    for line in lines:
        subtotal += line.base_unit_price * line.quantity
    subtotal_discount = Money(Decimal(discount), currency)
    expected_subtotal = max(subtotal - subtotal_discount, zero_money(currency))

    # when
    apply_subtotal_discount_to_order_lines(lines, subtotal, subtotal_discount)

    # then
    discounted_subtotal = zero_money(currency)
    for line in lines:
        discounted_subtotal += line.total_price_net
    assert discounted_subtotal == expected_subtotal

    assert (
        discounted_subtotal.amount
        == lines[0].total_price_net_amount + lines[1].total_price_net_amount
    )
    assert (
        discounted_subtotal.amount
        == lines[0].total_price_gross_amount + lines[1].total_price_gross_amount
    )

    assert lines[0].total_price_net_amount == _quantize(
        lines[0].unit_price_net_amount * lines[0].quantity
    )
    assert lines[0].total_price_gross_amount == _quantize(
        lines[0].unit_price_gross_amount * lines[0].quantity
    )
    assert lines[1].total_price_net_amount == _quantize(
        lines[1].unit_price_net_amount * lines[1].quantity
    )
    assert lines[1].total_price_gross_amount == _quantize(
        lines[1].unit_price_gross_amount * lines[1].quantity
    )
    assert (
        max(
            lines[0].base_unit_price * lines[0].quantity
            + lines[1].base_unit_price * lines[1].quantity
            - subtotal_discount,
            zero_money(currency),
        )
        == expected_subtotal
    )


@pytest.mark.parametrize("discount", ["10", "1", "17.3", "10000", "0"])
def test_apply_subtotal_discount_to_order_lines_order_with_single_line(
    discount,
    order_with_lines,
    voucher,
):
    # given
    order = order_with_lines
    currency = order.currency

    def _quantize(price):
        return quantize_price(price, currency)

    order.lines.all()[1].delete()
    line = order.lines.first()
    subtotal = line.base_unit_price * line.quantity
    subtotal_discount = Money(Decimal(discount), currency)
    expected_subtotal = max(subtotal - subtotal_discount, zero_money(currency))

    # when
    apply_subtotal_discount_to_order_lines([line], subtotal, subtotal_discount)

    # then
    discounted_subtotal = line.total_price_net
    assert discounted_subtotal == expected_subtotal
    assert discounted_subtotal.amount == line.total_price_net_amount
    assert discounted_subtotal.amount == line.total_price_gross_amount

    assert line.total_price_net_amount == _quantize(
        line.unit_price_net_amount * line.quantity
    )
    assert line.total_price_gross_amount == _quantize(
        line.unit_price_gross_amount * line.quantity
    )
    assert (
        max(
            line.base_unit_price * line.quantity - subtotal_discount,
            zero_money(currency),
        )
        == line.total_price_net
    )
