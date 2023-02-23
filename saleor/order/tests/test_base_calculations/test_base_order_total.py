from decimal import ROUND_HALF_UP, Decimal

from prices import Money

from ....core.taxes import zero_money
from ....discount import DiscountValueType, OrderDiscountType
from ... import base_calculations


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


def test_base_order_total_with_fixed_voucher(order_with_lines):
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
        type=OrderDiscountType.VOUCHER,
        value_type=DiscountValueType.FIXED,
        value=discount_amount,
        name="Voucher",
        translated_name="VoucherPL",
        currency=order.currency,
        amount_value=0,
    )

    # when
    order_total = base_calculations.base_order_total(order, lines)

    # then
    assert order_total == undiscounted_total - Money(discount_amount, order.currency)
    order_discount.refresh_from_db()
    assert order_discount.amount_value == discount_amount


def test_base_order_total_with_fixed_voucher_more_then_total(order_with_lines):
    # given
    order = order_with_lines
    lines = order.lines.all()
    shipping_price = order.shipping_price.net
    subtotal = zero_money(order.currency)
    for line in lines:
        subtotal += line.base_unit_price * line.quantity

    order_discount = order.discounts.create(
        type=OrderDiscountType.VOUCHER,
        value_type=DiscountValueType.FIXED,
        value=100,
        name="Voucher",
        translated_name="VoucherPL",
        currency=order.currency,
        amount_value=0,
    )

    # when
    order_total = base_calculations.base_order_total(order, lines)

    # then
    # Voucher isn't applied on shipping price
    assert order_total == shipping_price
    order_discount.refresh_from_db()
    assert order_discount.amount == subtotal


def test_base_order_total_with_percentage_voucher(order_with_lines):
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
        type=OrderDiscountType.VOUCHER,
        value_type=DiscountValueType.PERCENTAGE,
        value=50,
        name="Voucher",
        translated_name="VoucherPL",
        currency=order.currency,
        amount_value=0,
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
        type=OrderDiscountType.MANUAL,
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

    order.discounts.create(
        type=OrderDiscountType.MANUAL,
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
        type=OrderDiscountType.MANUAL,
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
        type=OrderDiscountType.MANUAL,
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
    order_with_lines,
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
        type=OrderDiscountType.VOUCHER,
        value_type=DiscountValueType.FIXED,
        value=voucher_discount_amount,
        name="StaffDiscount",
        translated_name="StaffDiscountPL",
        currency=order.currency,
        amount_value=0,
    )
    manual_discount_amount = 10
    manual_order_discount = order.discounts.create(
        type=OrderDiscountType.MANUAL,
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
    order_with_lines,
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
        type=OrderDiscountType.VOUCHER,
        value_type=DiscountValueType.PERCENTAGE,
        value=50,
        name="StaffDiscount",
        translated_name="StaffDiscountPL",
        currency=order.currency,
        amount_value=0,
    )
    manual_discount_amount = 10
    manual_order_discount = order.discounts.create(
        type=OrderDiscountType.MANUAL,
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
    order_with_lines,
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
        type=OrderDiscountType.VOUCHER,
        value_type=DiscountValueType.FIXED,
        value=10,
        name="StaffDiscount",
        translated_name="StaffDiscountPL",
        currency=order.currency,
        amount_value=0,
    )
    temporary_total = undiscounted_total - Money(
        voucher_discount_amount, order.currency
    )
    manual_discount_amount = temporary_total.amount * Decimal(0.5)
    manual_order_discount = order.discounts.create(
        type=OrderDiscountType.MANUAL,
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
    order_with_lines,
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
        type=OrderDiscountType.VOUCHER,
        value_type=DiscountValueType.PERCENTAGE,
        value=50,
        name="StaffDiscount",
        translated_name="StaffDiscountPL",
        currency=order.currency,
        amount_value=0,
    )

    temporary_total = undiscounted_total - Money(
        voucher_discount_amount, order.currency
    )
    manual_discount_amount = temporary_total.amount * Decimal(0.5)
    manual_order_discount = order.discounts.create(
        type=OrderDiscountType.MANUAL,
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
    order_with_lines,
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
        type=OrderDiscountType.MANUAL,
        value_type=DiscountValueType.FIXED,
        value=manual_discount_amount,
        name="StaffDiscount",
        translated_name="StaffDiscountPL",
        currency=order.currency,
        amount_value=0,
    )

    voucher_discount_amount = 10
    voucher_order_discount = order.discounts.create(
        type=OrderDiscountType.VOUCHER,
        value_type=DiscountValueType.FIXED,
        value=voucher_discount_amount,
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
    manual_order_discount.refresh_from_db()
    assert manual_order_discount.amount_value == manual_discount_amount
    voucher_order_discount.refresh_from_db()
    assert voucher_order_discount.amount_value == voucher_discount_amount


def test_base_order_total_with_fixed_manual_discount_and_percentage_voucher(
    order_with_lines,
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
        type=OrderDiscountType.MANUAL,
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
        type=OrderDiscountType.VOUCHER,
        value_type=DiscountValueType.PERCENTAGE,
        value=50,
        name="StaffDiscount",
        translated_name="StaffDiscountPL",
        currency=order.currency,
        amount_value=voucher_discount_amount,
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
    order_with_lines,
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
        type=OrderDiscountType.MANUAL,
        value_type=DiscountValueType.PERCENTAGE,
        value=50,
        name="StaffDiscount",
        translated_name="StaffDiscountPL",
        currency=order.currency,
        amount_value=0,
    )

    voucher_discount_amount = 10
    voucher_order_discount = order.discounts.create(
        type=OrderDiscountType.VOUCHER,
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
    manual_order_discount.refresh_from_db()
    assert manual_order_discount.amount_value == manual_discount_amount
    voucher_order_discount.refresh_from_db()
    assert voucher_order_discount.amount_value == voucher_discount_amount


def test_base_order_total_with_percentage_manual_discount_and_percentage_voucher(
    order_with_lines,
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
        type=OrderDiscountType.MANUAL,
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
        type=OrderDiscountType.VOUCHER,
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
    manual_order_discount.refresh_from_db()
    assert manual_order_discount.amount_value == manual_discount_amount
    voucher_order_discount.refresh_from_db()
    assert voucher_order_discount.amount_value == voucher_discount_amount
