from decimal import ROUND_HALF_UP, Decimal

import pytest
from prices import Money

from ....core.taxes import zero_money
from ....discount import DiscountType, DiscountValueType
from ... import base_calculations
from ...base_calculations import apply_subtotal_discount_to_order_lines


def test_base_order_total(order_with_lines):
    # given
    order = order_with_lines
    lines = order.lines.all()
    shipping_price = order.shipping_price.net
    subtotal = zero_money(order.currency)
    for line in lines:
        subtotal += line.base_unit_price * line.quantity
    undiscounted_total = subtotal + shipping_price

    # when
    order_total = base_calculations.base_order_total(order, lines)

    # then
    assert order_total == undiscounted_total


def test_base_order_total_with_fixed_voucher(order_with_lines, voucher):
    # given
    order = order_with_lines
    lines = order.lines.all()
    shipping_price = order.shipping_price.net
    subtotal = zero_money(order.currency)
    for line in lines:
        subtotal += line.base_unit_price * line.quantity
    undiscounted_total = subtotal + shipping_price

    discount_amount = 10
    order_discount = order.discounts.create(
        type=DiscountType.VOUCHER,
        value_type=DiscountValueType.FIXED,
        value=discount_amount,
        name="Voucher",
        translated_name="VoucherPL",
        currency=order.currency,
        amount_value=0,
        voucher=voucher,
    )

    # when
    order_total = base_calculations.base_order_total(order, lines)

    # then
    assert order_total == undiscounted_total - Money(discount_amount, order.currency)
    order_discount.refresh_from_db()
    assert order_discount.amount_value == discount_amount


def test_base_order_total_with_fixed_voucher_more_then_total(order_with_lines, voucher):
    # given
    order = order_with_lines
    lines = order.lines.all()
    shipping_price = order.shipping_price.net
    subtotal = zero_money(order.currency)
    for line in lines:
        subtotal += line.base_unit_price * line.quantity

    order_discount = order.discounts.create(
        type=DiscountType.VOUCHER,
        value_type=DiscountValueType.FIXED,
        value=100,
        name="Voucher",
        translated_name="VoucherPL",
        currency=order.currency,
        amount_value=0,
        voucher=voucher,
    )

    # when
    order_total = base_calculations.base_order_total(order, lines)

    # then
    # Voucher isn't applied on shipping price
    assert order_total == shipping_price
    order_discount.refresh_from_db()
    assert order_discount.amount == subtotal


def test_base_order_total_with_percentage_voucher(order_with_lines, voucher):
    # given
    order = order_with_lines
    lines = order.lines.all()
    shipping_price = order.shipping_price.net
    subtotal = zero_money(order.currency)
    for line in lines:
        subtotal += line.base_unit_price * line.quantity
    undiscounted_total = subtotal + shipping_price

    discount_amount = subtotal.amount * Decimal(0.5)
    order_discount = order.discounts.create(
        type=DiscountType.VOUCHER,
        value_type=DiscountValueType.PERCENTAGE,
        value=50,
        name="Voucher",
        translated_name="VoucherPL",
        currency=order.currency,
        amount_value=0,
        voucher=voucher,
    )

    # when
    order_total = base_calculations.base_order_total(order, lines)

    # then
    assert order_total == undiscounted_total - Money(discount_amount, order.currency)
    order_discount.refresh_from_db()
    assert order_discount.amount_value == discount_amount


def test_base_order_total_with_fixed_manual_discount(order_with_lines):
    # given
    order = order_with_lines
    lines = order.lines.all()
    shipping_price = order.shipping_price.net
    subtotal = zero_money(order.currency)
    for line in lines:
        subtotal += line.base_unit_price * line.quantity
    undiscounted_total = subtotal + shipping_price

    discount_amount = 10
    order_discount = order.discounts.create(
        type=DiscountType.MANUAL,
        value_type=DiscountValueType.FIXED,
        value=10,
        name="StaffDiscount",
        translated_name="StaffDiscountPL",
        currency=order.currency,
        amount_value=0,
    )

    # when
    order_total = base_calculations.base_order_total(order, lines)

    # then
    assert order_total == undiscounted_total - Money(discount_amount, order.currency)
    order_discount.refresh_from_db()
    assert order_discount.amount_value == discount_amount


def test_base_order_total_with_fixed_manual_discount_and_zero_order_total(order):
    # given
    lines = order.lines.all()
    assert not lines

    order.discounts.create(
        type=DiscountType.MANUAL,
        value_type=DiscountValueType.FIXED,
        value=0,
        name="StaffDiscount",
        translated_name="StaffDiscountPL",
        currency=order.currency,
        amount_value=0,
    )

    # when
    order_total = base_calculations.base_order_total(order, lines)

    # then
    assert order_total == zero_money(order.currency)


def test_base_order_total_with_fixed_manual_discount_more_then_total(order_with_lines):
    # given
    order = order_with_lines
    lines = order.lines.all()
    shipping_price = order.shipping_price.net
    subtotal = zero_money(order.currency)
    for line in lines:
        subtotal += line.base_unit_price * line.quantity
    undiscounted_total = subtotal + shipping_price

    order_discount = order.discounts.create(
        type=DiscountType.MANUAL,
        value_type=DiscountValueType.FIXED,
        value=100,
        name="StaffDiscount",
        translated_name="StaffDiscountPL",
        currency=order.currency,
        amount_value=0,
    )

    # when
    order_total = base_calculations.base_order_total(order, lines)

    # then
    assert order_total == Money(Decimal("0"), order.currency)
    order_discount.refresh_from_db()
    assert order_discount.amount == undiscounted_total


def test_base_order_total_with_percentage_manual_discount(order_with_lines):
    # given
    order = order_with_lines
    lines = order.lines.all()
    shipping_price = order.shipping_price.net
    subtotal = zero_money(order.currency)
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
        currency=order.currency,
        amount_value=0,
    )

    # when
    order_total = base_calculations.base_order_total(order, lines)

    # then
    assert order_total == undiscounted_total - Money(discount_amount, order.currency)
    order_discount.refresh_from_db()
    assert order_discount.amount_value == discount_amount


def test_base_order_total_with_fixed_voucher_and_fixed_manual_discount(
    order_with_lines, voucher
):
    # given
    order = order_with_lines
    lines = order.lines.all()
    shipping_price = order.shipping_price.net
    subtotal = zero_money(order.currency)
    for line in lines:
        subtotal += line.base_unit_price * line.quantity
    undiscounted_total = subtotal + shipping_price

    voucher_discount_amount = 10
    voucher_order_discount = order.discounts.create(
        type=DiscountType.VOUCHER,
        value_type=DiscountValueType.FIXED,
        value=voucher_discount_amount,
        name="StaffDiscount",
        translated_name="StaffDiscountPL",
        currency=order.currency,
        amount_value=0,
        voucher=voucher,
    )
    manual_discount_amount = 10
    manual_order_discount = order.discounts.create(
        type=DiscountType.MANUAL,
        value_type=DiscountValueType.FIXED,
        value=manual_discount_amount,
        name="StaffDiscount",
        translated_name="StaffDiscountPL",
        currency=order.currency,
        amount_value=0,
    )

    # when
    order_total = base_calculations.base_order_total(order, lines)

    # then
    assert order_total == undiscounted_total - Money(
        voucher_discount_amount, order.currency
    ) - Money(manual_discount_amount, order.currency)
    voucher_order_discount.refresh_from_db()
    assert voucher_order_discount.amount_value == voucher_discount_amount
    manual_order_discount.refresh_from_db()
    assert manual_order_discount.amount_value == manual_discount_amount


def test_base_order_total_with_percentage_voucher_and_fixed_manual_discount(
    order_with_lines, voucher
):
    # given
    order = order_with_lines
    lines = order.lines.all()
    shipping_price = order.shipping_price.net
    subtotal = zero_money(order.currency)
    for line in lines:
        subtotal += line.base_unit_price * line.quantity
    undiscounted_total = subtotal + shipping_price

    voucher_discount_amount = subtotal.amount * Decimal(0.5)
    voucher_order_discount = order.discounts.create(
        type=DiscountType.VOUCHER,
        value_type=DiscountValueType.PERCENTAGE,
        value=50,
        name="StaffDiscount",
        translated_name="StaffDiscountPL",
        currency=order.currency,
        amount_value=0,
        voucher=voucher,
    )
    manual_discount_amount = 10
    manual_order_discount = order.discounts.create(
        type=DiscountType.MANUAL,
        value_type=DiscountValueType.FIXED,
        value=10,
        name="StaffDiscount",
        translated_name="StaffDiscountPL",
        currency=order.currency,
        amount_value=0,
    )

    # when
    order_total = base_calculations.base_order_total(order, lines)

    # then
    assert order_total == undiscounted_total - Money(
        voucher_discount_amount, order.currency
    ) - Money(manual_discount_amount, order.currency)
    voucher_order_discount.refresh_from_db()
    assert voucher_order_discount.amount_value == voucher_discount_amount
    manual_order_discount.refresh_from_db()
    assert manual_order_discount.amount_value == manual_discount_amount


def test_base_order_total_with_fixed_voucher_and_percentage_manual_discount(
    order_with_lines, voucher
):
    # given
    order = order_with_lines
    lines = order.lines.all()
    shipping_price = order.shipping_price.net
    subtotal = zero_money(order.currency)
    for line in lines:
        subtotal += line.base_unit_price * line.quantity
    undiscounted_total = subtotal + shipping_price

    voucher_discount_amount = 10
    voucher_order_discount = order.discounts.create(
        type=DiscountType.VOUCHER,
        value_type=DiscountValueType.FIXED,
        value=10,
        name="StaffDiscount",
        translated_name="StaffDiscountPL",
        currency=order.currency,
        amount_value=0,
        voucher=voucher,
    )
    temporary_total = undiscounted_total - Money(
        voucher_discount_amount, order.currency
    )
    manual_discount_amount = temporary_total.amount * Decimal(0.5)
    manual_order_discount = order.discounts.create(
        type=DiscountType.MANUAL,
        value_type=DiscountValueType.PERCENTAGE,
        value=50,
        name="StaffDiscount",
        translated_name="StaffDiscountPL",
        currency=order.currency,
        amount_value=0,
    )

    # when
    order_total = base_calculations.base_order_total(order, lines)

    # then
    assert order_total == undiscounted_total - Money(
        voucher_discount_amount, order.currency
    ) - Money(manual_discount_amount, order.currency)
    voucher_order_discount.refresh_from_db()
    assert voucher_order_discount.amount_value == voucher_discount_amount
    manual_order_discount.refresh_from_db()
    assert manual_order_discount.amount_value == manual_discount_amount


def test_base_order_total_with_percentage_voucher_and_percentage_manual_discount(
    order_with_lines, voucher
):
    # given
    order = order_with_lines
    lines = order.lines.all()
    shipping_price = order.shipping_price.net
    subtotal = zero_money(order.currency)
    for line in lines:
        subtotal += line.base_unit_price * line.quantity
    undiscounted_total = subtotal + shipping_price

    voucher_discount_amount = subtotal.amount * Decimal(0.5)
    voucher_order_discount = order.discounts.create(
        type=DiscountType.VOUCHER,
        value_type=DiscountValueType.PERCENTAGE,
        value=50,
        name="StaffDiscount",
        translated_name="StaffDiscountPL",
        currency=order.currency,
        amount_value=0,
        voucher=voucher,
    )

    temporary_total = undiscounted_total - Money(
        voucher_discount_amount, order.currency
    )
    manual_discount_amount = temporary_total.amount * Decimal(0.5)
    manual_order_discount = order.discounts.create(
        type=DiscountType.MANUAL,
        value_type=DiscountValueType.PERCENTAGE,
        value=50,
        name="StaffDiscount",
        translated_name="StaffDiscountPL",
        currency=order.currency,
        amount_value=0,
    )

    # when
    order_total = base_calculations.base_order_total(order, lines)

    # then
    assert order_total == undiscounted_total - Money(
        voucher_discount_amount, order.currency
    ) - Money(manual_discount_amount, order.currency)
    voucher_order_discount.refresh_from_db()
    assert voucher_order_discount.amount_value == voucher_discount_amount
    manual_order_discount.refresh_from_db()
    assert manual_order_discount.amount_value == manual_discount_amount


def test_base_order_total_with_fixed_manual_discount_and_fixed_voucher(
    order_with_lines, voucher
):
    # given
    order = order_with_lines
    lines = order.lines.all()
    shipping_price = order.shipping_price.net
    subtotal = zero_money(order.currency)
    for line in lines:
        subtotal += line.base_unit_price * line.quantity
    undiscounted_total = subtotal + shipping_price

    manual_discount_amount = 10
    manual_order_discount = order.discounts.create(
        type=DiscountType.MANUAL,
        value_type=DiscountValueType.FIXED,
        value=manual_discount_amount,
        name="StaffDiscount",
        translated_name="StaffDiscountPL",
        currency=order.currency,
        amount_value=0,
    )

    voucher_discount_amount = 10
    voucher_order_discount = order.discounts.create(
        type=DiscountType.VOUCHER,
        value_type=DiscountValueType.FIXED,
        value=voucher_discount_amount,
        name="StaffDiscount",
        translated_name="StaffDiscountPL",
        currency=order.currency,
        amount_value=0,
        voucher=voucher,
    )

    # when
    order_total = base_calculations.base_order_total(order, lines)

    # then
    assert order_total == undiscounted_total - Money(
        voucher_discount_amount, order.currency
    ) - Money(manual_discount_amount, order.currency)
    manual_order_discount.refresh_from_db()
    assert manual_order_discount.amount_value == manual_discount_amount
    voucher_order_discount.refresh_from_db()
    assert voucher_order_discount.amount_value == voucher_discount_amount


def test_base_order_total_with_fixed_manual_discount_and_percentage_voucher(
    order_with_lines, voucher
):
    # given
    order = order_with_lines
    lines = order.lines.all()
    shipping_price = order.shipping_price.net
    subtotal = zero_money(order.currency)
    for line in lines:
        subtotal += line.base_unit_price * line.quantity
    undiscounted_total = subtotal + shipping_price

    manual_discount_amount = 10
    manual_order_discount = order.discounts.create(
        type=DiscountType.MANUAL,
        value_type=DiscountValueType.FIXED,
        value=10,
        name="StaffDiscount",
        translated_name="StaffDiscountPL",
        currency=order.currency,
        amount_value=manual_discount_amount,
    )

    subtotal_discount_from_order_discount = (
        subtotal / undiscounted_total * manual_discount_amount
    )
    temporary_subtotal_amount = subtotal.amount - subtotal_discount_from_order_discount
    voucher_discount_amount = (temporary_subtotal_amount * Decimal(0.5)).quantize(
        Decimal("0.01"), ROUND_HALF_UP
    )
    voucher_order_discount = order.discounts.create(
        type=DiscountType.VOUCHER,
        value_type=DiscountValueType.PERCENTAGE,
        value=50,
        name="StaffDiscount",
        translated_name="StaffDiscountPL",
        currency=order.currency,
        amount_value=voucher_discount_amount,
        voucher=voucher,
    )

    # when
    order_total = base_calculations.base_order_total(order, lines)

    # then
    assert voucher_discount_amount == Decimal("30.63")
    expected_total = (
        undiscounted_total
        - Money(voucher_discount_amount, order.currency)
        - Money(manual_discount_amount, order.currency)
    )
    assert order_total == expected_total
    manual_order_discount.refresh_from_db()
    assert manual_order_discount.amount_value == manual_discount_amount
    voucher_order_discount.refresh_from_db()
    assert voucher_order_discount.amount_value == voucher_discount_amount


def test_base_order_total_with_percentage_manual_discount_and_fixed_voucher(
    order_with_lines, voucher
):
    # given
    order = order_with_lines
    lines = order.lines.all()
    shipping_price = order.shipping_price.net
    subtotal = zero_money(order.currency)
    for line in lines:
        subtotal += line.base_unit_price * line.quantity
    undiscounted_total = subtotal + shipping_price

    manual_discount_amount = undiscounted_total.amount * Decimal(0.5)
    manual_order_discount = order.discounts.create(
        type=DiscountType.MANUAL,
        value_type=DiscountValueType.PERCENTAGE,
        value=50,
        name="StaffDiscount",
        translated_name="StaffDiscountPL",
        currency=order.currency,
        amount_value=0,
    )

    voucher_discount_amount = 10
    voucher_order_discount = order.discounts.create(
        type=DiscountType.VOUCHER,
        value_type=DiscountValueType.FIXED,
        value=10,
        name="StaffDiscount",
        translated_name="StaffDiscountPL",
        currency=order.currency,
        amount_value=0,
        voucher=voucher,
    )

    # when
    order_total = base_calculations.base_order_total(order, lines)

    # then
    assert order_total == undiscounted_total - Money(
        voucher_discount_amount, order.currency
    ) - Money(manual_discount_amount, order.currency)
    manual_order_discount.refresh_from_db()
    assert manual_order_discount.amount_value == manual_discount_amount
    voucher_order_discount.refresh_from_db()
    assert voucher_order_discount.amount_value == voucher_discount_amount


def test_base_order_total_with_percentage_manual_discount_and_percentage_voucher(
    order_with_lines,
    voucher,
):
    # given
    order = order_with_lines
    lines = order.lines.all()
    shipping_price = order.shipping_price.net
    subtotal = zero_money(order.currency)
    for line in lines:
        subtotal += line.base_unit_price * line.quantity
    undiscounted_total = subtotal + shipping_price

    manual_discount_amount = undiscounted_total.amount * Decimal(0.5)
    manual_order_discount = order.discounts.create(
        type=DiscountType.MANUAL,
        value_type=DiscountValueType.PERCENTAGE,
        value=50,
        name="StaffDiscount",
        translated_name="StaffDiscountPL",
        currency=order.currency,
        amount_value=0,
    )

    temporary_subtotal_amount = subtotal.amount * Decimal(0.5)
    voucher_discount_amount = temporary_subtotal_amount * Decimal(0.5)
    voucher_order_discount = order.discounts.create(
        type=DiscountType.VOUCHER,
        value_type=DiscountValueType.PERCENTAGE,
        value=50,
        name="StaffDiscount",
        translated_name="StaffDiscountPL",
        currency=order.currency,
        amount_value=0,
        voucher=voucher,
    )

    # when
    order_total = base_calculations.base_order_total(order, lines)

    # then
    assert order_total == undiscounted_total - Money(
        voucher_discount_amount, order.currency
    ) - Money(manual_discount_amount, order.currency)
    manual_order_discount.refresh_from_db()
    assert manual_order_discount.amount_value == manual_discount_amount
    voucher_order_discount.refresh_from_db()
    assert voucher_order_discount.amount_value == voucher_discount_amount


def test_base_order_total_with_shipping_voucher(
    order_with_lines, voucher_shipping_type
):
    # given
    order = order_with_lines
    lines = order.lines.all()
    shipping_price = order.shipping_price.net
    subtotal = zero_money(order.currency)
    for line in lines:
        subtotal += line.base_unit_price * line.quantity
    undiscounted_total = subtotal + shipping_price

    discount_amount = 5
    order_discount = order.discounts.create(
        type=DiscountType.VOUCHER,
        value_type=DiscountValueType.FIXED,
        value=discount_amount,
        name="Voucher",
        translated_name="VoucherPL",
        currency=order.currency,
        amount_value=0,
        voucher=voucher_shipping_type,
    )

    # when
    order_total = base_calculations.base_order_total(order, lines)

    # then
    assert order_total == undiscounted_total - Money(discount_amount, order.currency)
    order_discount.refresh_from_db()
    assert order_discount.amount_value == discount_amount


def test_apply_order_discounts_with_shipping_voucher(
    order_with_lines, voucher_shipping_type
):
    # given
    order = order_with_lines
    lines = order.lines.all()
    shipping_price = order.shipping_price.net
    subtotal = zero_money(order.currency)
    for line in lines:
        subtotal += line.base_unit_price * line.quantity

    discount_amount = 5
    order_discount = order.discounts.create(
        type=DiscountType.VOUCHER,
        value_type=DiscountValueType.FIXED,
        value=discount_amount,
        name="Voucher",
        translated_name="VoucherPL",
        currency=order.currency,
        amount_value=0,
        voucher=voucher_shipping_type,
    )

    # when
    (
        discounted_subtotal,
        discounted_shipping_price,
    ) = base_calculations.apply_order_discounts(subtotal, shipping_price, order)

    # then
    assert discounted_subtotal == subtotal
    assert discounted_shipping_price == shipping_price - Money(
        discount_amount, order.currency
    )
    order_discount.refresh_from_db()
    assert order_discount.amount_value == discount_amount


def test_apply_order_discounts_with_entire_order_voucher(order_with_lines, voucher):
    # given
    order = order_with_lines
    lines = order.lines.all()
    shipping_price = order.shipping_price.net
    subtotal = zero_money(order.currency)
    for line in lines:
        subtotal += line.base_unit_price * line.quantity

    discount_amount = 10
    order_discount = order.discounts.create(
        type=DiscountType.VOUCHER,
        value_type=DiscountValueType.FIXED,
        value=discount_amount,
        name="Voucher",
        translated_name="VoucherPL",
        currency=order.currency,
        amount_value=0,
        voucher=voucher,
    )

    # when
    (
        discounted_subtotal,
        discounted_shipping_price,
    ) = base_calculations.apply_order_discounts(subtotal, shipping_price, order)

    # then
    assert discounted_subtotal == subtotal - Money(discount_amount, order.currency)
    assert discounted_shipping_price == shipping_price
    order_discount.refresh_from_db()
    assert order_discount.amount_value == discount_amount


@pytest.mark.parametrize("discount", ["10", "1", "17.3", "10000", "0"])
def test_apply_subtotal_discount_to_order_lines(
    discount,
    order_with_lines,
    voucher,
):
    # given
    order = order_with_lines
    currency = order.currency
    lines = order.lines.all()
    subtotal = zero_money(currency)
    for line in lines:
        subtotal += line.base_unit_price * line.quantity
    subtotal_discount = Money(Decimal(discount), currency)
    expected_subtotal = max(subtotal - subtotal_discount, zero_money(currency))
    line_0_share = lines[0].total_price_net_amount / subtotal.amount

    # when
    apply_subtotal_discount_to_order_lines(lines, subtotal, subtotal_discount)

    # then
    discounted_subtotal = zero_money(currency)
    for line in lines:
        discounted_subtotal += line.base_unit_price * line.quantity
    assert discounted_subtotal == expected_subtotal

    line_0_total_price_net = round(lines[0].total_price_net_amount, 5)
    line_0_total_price_gross = round(lines[0].total_price_gross_amount, 5)
    line_0_unit_price_net = round(lines[0].unit_price_net_amount, 5)
    line_0_unit_price_gross = round(lines[0].unit_price_gross_amount, 5)
    line_0_base_unit_price = round(lines[0].base_unit_price_amount, 5)
    line_0_unit_discount = round(lines[0].unit_discount_amount, 5)
    line_0_quantity = lines[0].quantity
    line_0_total_discount = line_0_unit_discount * line_0_quantity

    line_1_total_price_net = round(lines[1].total_price_net_amount, 5)
    line_1_total_price_gross = round(lines[1].total_price_gross_amount, 5)

    assert discounted_subtotal.amount == line_0_total_price_net + line_1_total_price_net
    assert (
        discounted_subtotal.amount
        == line_0_total_price_gross + line_1_total_price_gross
    )

    max_diff = 0.00001
    assert (
        abs(round(line_0_share * subtotal_discount.amount, 5) - line_0_total_discount)
        <= max_diff
    )
    assert (
        abs(line_0_total_price_net - (line_0_unit_price_net * line_0_quantity))
        <= max_diff
    )
    assert (
        abs(line_0_total_price_gross - (line_0_unit_price_gross * line_0_quantity))
        <= max_diff
    )
    assert line_0_base_unit_price == line_0_unit_price_net


def test_apply_subtotal_discount_to_order_lines_order_with_single_line(
    order_with_lines,
    voucher,
):
    # given
    order = order_with_lines
    order.lines.last().delete()
    currency = order.currency

    lines = order.lines.all()
    assert lines.count() == 1
    subtotal = lines[0].base_unit_price * lines[0].quantity
    subtotal_discount = Money(Decimal("10"), currency)
    discounted_subtotal = subtotal - subtotal_discount

    # when
    apply_subtotal_discount_to_order_lines(lines, subtotal, subtotal_discount)

    # then
    assert lines[0].base_unit_price * lines[0].quantity == subtotal - subtotal_discount

    line_0_total_price_net = round(lines[0].total_price_net_amount, 5)
    line_0_total_price_gross = round(lines[0].total_price_gross_amount, 5)
    line_0_unit_price_net = round(lines[0].unit_price_net_amount, 5)
    line_0_unit_price_gross = round(lines[0].unit_price_gross_amount, 5)
    line_0_base_unit_price = round(lines[0].base_unit_price_amount, 5)
    line_0_unit_discount = round(lines[0].unit_discount_amount, 5)
    line_0_quantity = lines[0].quantity
    line_0_total_discount = line_0_unit_discount * line_0_quantity

    assert line_0_total_price_net == discounted_subtotal.amount
    assert line_0_total_price_gross == discounted_subtotal.amount

    max_diff = 0.00001
    assert abs(line_0_total_discount - subtotal_discount.amount) <= max_diff
    assert (
        abs(line_0_unit_price_net - (line_0_total_price_net / line_0_quantity))
        <= max_diff
    )
    assert (
        abs(line_0_unit_price_gross - (line_0_total_price_gross / line_0_quantity))
        <= max_diff
    )
    assert line_0_base_unit_price == line_0_unit_price_net
