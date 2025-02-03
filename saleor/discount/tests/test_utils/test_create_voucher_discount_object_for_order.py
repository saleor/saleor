from decimal import Decimal

import graphene

from ....core.prices import Money, quantize_price
from ....core.taxes import zero_money
from ....order import OrderStatus
from ....order.calculations import fetch_order_prices_if_expired
from ... import DiscountType, DiscountValueType, VoucherType
from ...models import (
    OrderDiscount,
    OrderLineDiscount,
    PromotionRule,
)
from ...utils.voucher import (
    create_or_update_voucher_discount_objects_for_order,
)


def test_create_discount_for_voucher_specific_product_fixed(
    order_with_lines,
    voucher_specific_product_type,
    plugins_manager,
    tax_configuration_flat_rates,
):
    # given
    order = order_with_lines
    order.status = OrderStatus.UNCONFIRMED
    voucher = voucher_specific_product_type
    tax_rate = Decimal("1.23")

    voucher_listing = voucher.channel_listings.get(channel=order.channel)
    unit_discount_amount = Decimal("5")
    voucher_listing.discount_value = unit_discount_amount
    voucher_listing.save(update_fields=["discount_value"])
    voucher.discount_value_type = DiscountValueType.FIXED
    voucher.save(update_fields=["discount_value_type"])

    lines = order.lines.all()
    discounted_line, line_1 = lines
    voucher.variants.add(discounted_line.variant)
    order.voucher = voucher
    order.voucher_code = voucher.codes.first().code

    shipping_price = order.shipping_price.net
    currency = order.currency
    subtotal = zero_money(currency)
    for line in lines:
        subtotal += line.base_unit_price * line.quantity

    # when
    create_or_update_voucher_discount_objects_for_order(order)
    order, lines = fetch_order_prices_if_expired(order, plugins_manager, None, True)

    # then
    discounted_line, line_1 = lines
    discount_amount = unit_discount_amount * discounted_line.quantity
    assert order.base_shipping_price == shipping_price
    assert order.shipping_price_net == shipping_price
    assert order.shipping_price_gross == shipping_price * tax_rate
    assert order.subtotal_net_amount == subtotal.amount - discount_amount
    assert order.subtotal_gross_amount == (subtotal.amount - discount_amount) * tax_rate
    assert (
        order.total_net_amount
        == order.subtotal_net_amount + order.base_shipping_price_amount
    )
    assert (
        order.total_gross_amount
        == (order.subtotal_net_amount + order.base_shipping_price_amount) * tax_rate
    )
    assert order.undiscounted_total_net == subtotal + shipping_price
    assert order.undiscounted_total_gross == (subtotal + shipping_price) * tax_rate

    assert (
        discounted_line.base_unit_price_amount
        == discounted_line.undiscounted_base_unit_price_amount - unit_discount_amount
    )
    assert (
        discounted_line.total_price_gross_amount
        == discounted_line.base_unit_price_amount * discounted_line.quantity * tax_rate
    )
    assert (
        discounted_line.undiscounted_total_price_gross_amount
        == discounted_line.undiscounted_base_unit_price_amount
        * discounted_line.quantity
        * tax_rate
    )
    assert discounted_line.unit_discount_amount == unit_discount_amount
    assert discounted_line.unit_discount_type == voucher.discount_value_type
    assert discounted_line.unit_discount_reason == f"Voucher code: {order.voucher_code}"
    assert discounted_line.unit_discount_value == unit_discount_amount

    assert line_1.base_unit_price_amount == line_1.undiscounted_base_unit_price_amount
    assert (
        line_1.total_price_gross_amount
        == line_1.undiscounted_base_unit_price_amount * line_1.quantity * tax_rate
    )
    assert (
        line_1.undiscounted_total_price_gross_amount
        == line_1.undiscounted_base_unit_price_amount * line_1.quantity * tax_rate
    )
    assert line_1.unit_discount_amount == 0
    assert line_1.unit_discount_value == 0
    assert line_1.unit_discount_type is None
    assert line_1.unit_discount_reason is None

    assert discounted_line.discounts.count() == 1
    line_discount = discounted_line.discounts.first()
    assert line_discount.amount_value == discount_amount
    assert (
        line_discount.value_type
        == DiscountValueType.FIXED
        == voucher.discount_value_type
    )
    assert line_discount.type == DiscountType.VOUCHER
    assert line_discount.reason == f"Voucher code: {order.voucher_code}"
    assert line_discount.value == unit_discount_amount


def test_create_discount_for_voucher_specific_product_percentage(
    order_with_lines,
    voucher_specific_product_type,
    plugins_manager,
    tax_configuration_flat_rates,
):
    # given
    order = order_with_lines
    order.status = OrderStatus.UNCONFIRMED
    voucher = voucher_specific_product_type
    tax_rate = Decimal("1.23")

    voucher_listing = voucher.channel_listings.get(channel=order.channel)
    discount_value = Decimal("10")
    voucher_listing.discount_value = discount_value
    voucher_listing.save(update_fields=["discount_value"])
    voucher.discount_value_type = DiscountValueType.PERCENTAGE
    voucher.save(update_fields=["discount_value_type"])

    lines = order.lines.all()
    discounted_line, line_1 = lines
    voucher.variants.add(discounted_line.variant)
    order.voucher = voucher
    order.voucher_code = voucher.codes.first().code

    shipping_price = order.shipping_price.net
    currency = order.currency
    subtotal = zero_money(currency)
    for line in lines:
        subtotal += line.base_unit_price * line.quantity

    # when
    create_or_update_voucher_discount_objects_for_order(order)
    order, lines = fetch_order_prices_if_expired(order, plugins_manager, None, True)

    # then
    discounted_line, line_1 = lines
    discount_amount = (
        discounted_line.undiscounted_base_unit_price_amount
        * discounted_line.quantity
        * discount_value
        / 100
    )
    assert order.base_shipping_price == shipping_price
    assert order.shipping_price_net == shipping_price
    assert order.shipping_price_gross == shipping_price * tax_rate
    assert order.subtotal_net_amount == subtotal.amount - discount_amount
    assert order.subtotal_gross_amount == (subtotal.amount - discount_amount) * tax_rate
    assert (
        order.total_net_amount
        == order.subtotal_net_amount + order.base_shipping_price_amount
    )
    assert (
        order.total_gross_amount
        == (order.subtotal_net_amount + order.base_shipping_price_amount) * tax_rate
    )
    assert order.undiscounted_total_net == subtotal + shipping_price
    assert order.undiscounted_total_gross == (subtotal + shipping_price) * tax_rate

    unit_discount_amount = discount_amount / discounted_line.quantity
    assert (
        discounted_line.base_unit_price_amount
        == discounted_line.undiscounted_base_unit_price_amount - unit_discount_amount
    )
    assert (
        discounted_line.total_price_gross_amount
        == discounted_line.base_unit_price_amount * discounted_line.quantity * tax_rate
    )
    assert (
        discounted_line.undiscounted_total_price_gross_amount
        == discounted_line.undiscounted_base_unit_price_amount
        * discounted_line.quantity
        * tax_rate
    )
    assert discounted_line.unit_discount_amount == unit_discount_amount
    assert discounted_line.unit_discount_type == DiscountValueType.PERCENTAGE
    assert discounted_line.unit_discount_reason == f"Voucher code: {order.voucher_code}"
    assert discounted_line.unit_discount_value == discount_value

    assert line_1.base_unit_price_amount == line_1.undiscounted_base_unit_price_amount
    assert (
        line_1.total_price_gross_amount
        == line_1.undiscounted_base_unit_price_amount * line_1.quantity * tax_rate
    )
    assert (
        line_1.undiscounted_total_price_gross_amount
        == line_1.undiscounted_base_unit_price_amount * line_1.quantity * tax_rate
    )
    assert line_1.unit_discount_amount == 0
    assert line_1.unit_discount_type is None
    assert line_1.unit_discount_reason is None

    assert discounted_line.discounts.count() == 1
    line_discount = discounted_line.discounts.first()
    assert line_discount.amount_value == discount_amount
    assert (
        line_discount.value_type
        == voucher.discount_value_type
        == DiscountValueType.PERCENTAGE
    )
    assert line_discount.type == DiscountType.VOUCHER
    assert line_discount.reason == f"Voucher code: {order.voucher_code}"
    assert line_discount.value == discount_value


def test_create_discount_for_voucher_apply_once_per_order_percentage(
    order_with_lines,
    voucher,
    plugins_manager,
    tax_configuration_flat_rates,
):
    # given
    order = order_with_lines
    order.status = OrderStatus.UNCONFIRMED
    tax_rate = Decimal("1.23")

    voucher_listing = voucher.channel_listings.get(channel=order.channel)
    discount_value = Decimal("10")
    voucher_listing.discount_value = discount_value
    voucher_listing.save(update_fields=["discount_value"])

    voucher.apply_once_per_order = True
    voucher.discount_value_type = DiscountValueType.PERCENTAGE
    voucher.save(update_fields=["discount_value_type", "apply_once_per_order"])

    lines = order.lines.all()
    order.voucher = voucher
    order.voucher_code = voucher.codes.first().code

    shipping_price = order.shipping_price.net
    currency = order.currency
    undiscounted_subtotal = zero_money(currency)
    for line in lines:
        undiscounted_subtotal += line.undiscounted_base_unit_price * line.quantity

    # when
    create_or_update_voucher_discount_objects_for_order(order)
    order, lines = fetch_order_prices_if_expired(order, plugins_manager, None, True)

    # then
    discounted_line, line_1 = lines
    discount_amount = (
        discounted_line.undiscounted_base_unit_price_amount * discount_value / 100
    )
    assert order.base_shipping_price == shipping_price
    assert order.shipping_price_net == shipping_price
    assert order.shipping_price_gross == shipping_price * tax_rate
    assert order.subtotal_net_amount == undiscounted_subtotal.amount - discount_amount
    assert (
        order.subtotal_gross_amount
        == (undiscounted_subtotal.amount - discount_amount) * tax_rate
    )
    assert (
        order.total_net_amount
        == order.subtotal_net_amount + order.base_shipping_price_amount
    )
    assert (
        order.total_gross_amount
        == (order.subtotal_net_amount + order.base_shipping_price_amount) * tax_rate
    )
    assert order.undiscounted_total_net == undiscounted_subtotal + shipping_price
    assert (
        order.undiscounted_total_gross
        == (undiscounted_subtotal + shipping_price) * tax_rate
    )

    unit_discount_amount = discount_amount / discounted_line.quantity
    assert quantize_price(
        discounted_line.base_unit_price_amount, currency
    ) == quantize_price(
        discounted_line.undiscounted_base_unit_price_amount - unit_discount_amount,
        currency,
    )
    assert discounted_line.total_price_gross_amount == quantize_price(
        discounted_line.base_unit_price_amount * discounted_line.quantity * tax_rate,
        currency,
    )
    assert (
        discounted_line.undiscounted_total_price_gross_amount
        == discounted_line.undiscounted_base_unit_price_amount
        * discounted_line.quantity
        * tax_rate
    )
    assert discounted_line.unit_discount_amount == unit_discount_amount
    assert discounted_line.unit_discount_type == DiscountValueType.PERCENTAGE
    assert discounted_line.unit_discount_reason == f"Voucher code: {order.voucher_code}"

    assert line_1.base_unit_price_amount == line_1.undiscounted_base_unit_price_amount
    assert (
        line_1.total_price_gross_amount
        == line_1.undiscounted_base_unit_price_amount * line_1.quantity * tax_rate
    )
    assert (
        line_1.undiscounted_total_price_gross_amount
        == line_1.undiscounted_base_unit_price_amount * line_1.quantity * tax_rate
    )
    assert line_1.unit_discount_amount == 0
    assert line_1.unit_discount_type is None
    assert line_1.unit_discount_reason is None

    assert discounted_line.discounts.count() == 1
    line_discount = discounted_line.discounts.first()
    assert line_discount.amount_value == discount_amount
    assert (
        line_discount.value_type
        == voucher.discount_value_type
        == DiscountValueType.PERCENTAGE
    )
    assert line_discount.type == DiscountType.VOUCHER
    assert line_discount.reason == f"Voucher code: {order.voucher_code}"
    assert line_discount.value == discount_value


def test_create_discount_for_voucher_apply_once_per_order_fixed(
    order_with_lines,
    voucher,
    plugins_manager,
    tax_configuration_flat_rates,
):
    # given
    order = order_with_lines
    order.status = OrderStatus.UNCONFIRMED
    tax_rate = Decimal("1.23")

    voucher_listing = voucher.channel_listings.get(channel=order.channel)
    discount_amount = Decimal("5")
    voucher_listing.discount_value = discount_amount
    voucher_listing.save(update_fields=["discount_value"])

    voucher.apply_once_per_order = True
    voucher.discount_value_type = DiscountValueType.FIXED
    voucher.save(update_fields=["discount_value_type", "apply_once_per_order"])

    lines = order.lines.all()
    order.voucher = voucher
    order.voucher_code = voucher.codes.first().code

    shipping_price = order.shipping_price.net
    currency = order.currency
    undiscounted_subtotal = zero_money(currency)
    for line in lines:
        undiscounted_subtotal += line.undiscounted_base_unit_price * line.quantity

    # when
    create_or_update_voucher_discount_objects_for_order(order)
    order, lines = fetch_order_prices_if_expired(order, plugins_manager, None, True)

    # then
    discounted_line, line_1 = lines
    assert order.base_shipping_price == shipping_price
    assert order.shipping_price_net == shipping_price
    assert order.shipping_price_gross == shipping_price * tax_rate
    assert order.subtotal_net_amount == undiscounted_subtotal.amount - discount_amount
    assert (
        order.subtotal_gross_amount
        == (undiscounted_subtotal.amount - discount_amount) * tax_rate
    )
    assert (
        order.total_net_amount
        == order.subtotal_net_amount + order.base_shipping_price_amount
    )
    assert (
        order.total_gross_amount
        == (order.subtotal_net_amount + order.base_shipping_price_amount) * tax_rate
    )
    assert order.undiscounted_total_net == undiscounted_subtotal + shipping_price
    assert (
        order.undiscounted_total_gross
        == (undiscounted_subtotal + shipping_price) * tax_rate
    )

    unit_discount_amount = discount_amount / discounted_line.quantity

    assert quantize_price(
        discounted_line.base_unit_price_amount, currency
    ) == quantize_price(
        discounted_line.undiscounted_base_unit_price_amount - unit_discount_amount,
        currency,
    )
    assert discounted_line.total_price_gross_amount == quantize_price(
        discounted_line.base_unit_price_amount * discounted_line.quantity * tax_rate,
        currency,
    )
    assert (
        discounted_line.undiscounted_total_price_gross_amount
        == discounted_line.undiscounted_base_unit_price_amount
        * discounted_line.quantity
        * tax_rate
    )
    assert discounted_line.unit_discount_amount == unit_discount_amount
    assert discounted_line.unit_discount_type == DiscountValueType.FIXED
    assert discounted_line.unit_discount_reason == f"Voucher code: {order.voucher_code}"

    assert line_1.base_unit_price_amount == line_1.undiscounted_base_unit_price_amount
    assert (
        line_1.total_price_gross_amount
        == line_1.undiscounted_base_unit_price_amount * line_1.quantity * tax_rate
    )
    assert (
        line_1.undiscounted_total_price_gross_amount
        == line_1.undiscounted_base_unit_price_amount * line_1.quantity * tax_rate
    )
    assert line_1.unit_discount_amount == 0
    assert line_1.unit_discount_type is None
    assert line_1.unit_discount_reason is None

    assert discounted_line.discounts.count() == 1
    line_discount = discounted_line.discounts.first()
    assert line_discount.amount_value == discount_amount
    assert line_discount.value_type == DiscountValueType.FIXED
    assert line_discount.type == DiscountType.VOUCHER
    assert line_discount.reason == f"Voucher code: {order.voucher_code}"
    assert line_discount.value == discount_amount


def test_create_discount_for_voucher_entire_order_fixed(
    order_with_lines,
    voucher,
    plugins_manager,
    tax_configuration_flat_rates,
):
    # given
    assert voucher.type == VoucherType.ENTIRE_ORDER
    assert voucher.discount_value_type == DiscountValueType.FIXED

    order = order_with_lines
    order.status = OrderStatus.UNCONFIRMED
    tax_rate = Decimal("1.23")

    voucher_listing = voucher.channel_listings.get(channel=order.channel)
    discount_amount = Decimal("35")
    voucher_listing.discount_value = discount_amount
    voucher_listing.save(update_fields=["discount_value"])

    voucher.name = "Voucher name"
    voucher.save(update_fields=["name"])

    order.voucher = voucher
    code = voucher.codes.first().code
    order.voucher_code = code

    shipping_price = order.shipping_price.net
    currency = order.currency
    subtotal = zero_money(currency)
    lines = order.lines.all()
    for line in lines:
        subtotal += line.base_unit_price * line.quantity

    # when
    create_or_update_voucher_discount_objects_for_order(order)
    order, lines = fetch_order_prices_if_expired(order, plugins_manager, None, True)

    # then
    assert OrderDiscount.objects.count() == 1
    discount = order.discounts.first()
    assert discount.voucher == voucher
    assert discount.value_type == voucher.discount_value_type
    assert discount.value == discount_amount
    assert discount.amount_value == discount_amount
    assert discount.reason == f"Voucher code: {code}"
    assert discount.name == voucher.name
    assert discount.type == DiscountType.VOUCHER
    assert discount.voucher_code == code
    # TODO (SHOPX-914): set translated voucher name
    assert discount.translated_name == ""

    assert order.base_shipping_price == shipping_price
    assert order.shipping_price_net == shipping_price
    assert order.shipping_price_gross == shipping_price * tax_rate
    assert order.subtotal_net_amount == subtotal.amount - discount_amount
    assert order.subtotal_gross_amount == (subtotal.amount - discount_amount) * tax_rate
    assert (
        order.total_net_amount
        == order.subtotal_net_amount + order.base_shipping_price_amount
    )
    assert (
        order.total_gross_amount
        == (order.subtotal_net_amount + order.base_shipping_price_amount) * tax_rate
    )
    assert order.undiscounted_total_net == subtotal + shipping_price
    assert order.undiscounted_total_gross == (subtotal + shipping_price) * tax_rate

    lines = order.lines.all()
    line_1 = [line for line in lines if line.quantity == 3][0]
    line_2 = [line for line in lines if line.quantity == 2][0]

    line_1_base_total = line_1.quantity * line_1.base_unit_price_amount
    line_2_base_total = line_2.quantity * line_2.base_unit_price_amount
    base_total = line_1_base_total + line_2_base_total
    line_1_order_discount_portion = discount_amount * line_1_base_total / base_total
    line_2_order_discount_portion = discount_amount - line_1_order_discount_portion

    variant_1 = line_1.variant
    variant_1_listing = variant_1.channel_listings.get(channel=order.channel)
    variant_1_undiscounted_unit_price = variant_1_listing.price_amount
    line_1_total_net_amount = quantize_price(
        line_1.undiscounted_total_price_net_amount - line_1_order_discount_portion,
        currency,
    )
    assert (
        line_1.undiscounted_total_price_net_amount
        == variant_1_undiscounted_unit_price * line_1.quantity
    )
    assert (
        line_1.undiscounted_unit_price_net_amount == variant_1_undiscounted_unit_price
    )
    assert line_1.total_price_net_amount == line_1_total_net_amount
    assert line_1.base_unit_price_amount == variant_1_undiscounted_unit_price
    assert line_1.unit_price_net_amount == line_1_total_net_amount / line_1.quantity

    variant_2 = line_2.variant
    variant_2_listing = variant_2.channel_listings.get(channel=order.channel)
    variant_2_undiscounted_unit_price = variant_2_listing.price_amount
    line_2_total_net_amount = quantize_price(
        line_2.undiscounted_total_price_net_amount - line_2_order_discount_portion,
        currency,
    )
    assert (
        line_2.undiscounted_total_price_net_amount
        == variant_2_undiscounted_unit_price * line_2.quantity
    )
    assert (
        line_2.undiscounted_unit_price_net_amount == variant_2_undiscounted_unit_price
    )
    assert line_2.total_price_net_amount == line_2_total_net_amount
    assert line_2.base_unit_price_amount == variant_2_undiscounted_unit_price
    assert line_2.unit_price_net_amount == line_2_total_net_amount / line_2.quantity


def test_create_discount_for_voucher_entire_order_multiple_lines(
    order,
    voucher,
    plugins_manager,
    order_lines_generator,
    product_list,
    tax_configuration_flat_rates,
):
    # given
    assert voucher.type == VoucherType.ENTIRE_ORDER
    assert voucher.discount_value_type == DiscountValueType.FIXED

    order.status = OrderStatus.UNCONFIRMED
    tax_rate = Decimal("1.23")

    voucher_listing = voucher.channel_listings.get(channel=order.channel)
    discount_amount = Decimal("3")
    voucher_listing.discount_value = discount_amount
    voucher_listing.save(update_fields=["discount_value"])

    voucher.name = "Voucher name"
    voucher.save(update_fields=["name"])

    code = voucher.codes.first().code
    order.voucher = voucher
    order.voucher_code = code

    shipping_price = order.shipping_price.net
    currency = order.currency

    variant_list = [product.variants.first() for product in product_list[:3]]
    unit_prices = [7, 33, 25]
    quantities = [1, 1, 1]
    lines = order_lines_generator(order, variant_list, unit_prices, quantities)

    subtotal = Money(sum(unit_prices), currency)

    # when
    create_or_update_voucher_discount_objects_for_order(order)
    order, lines = fetch_order_prices_if_expired(order, plugins_manager, None, True)

    # then
    assert OrderDiscount.objects.count() == 1
    discount = order.discounts.first()
    assert discount.voucher == voucher
    assert discount.value_type == voucher.discount_value_type
    assert discount.value == discount_amount
    assert discount.amount_value == discount_amount
    assert discount.reason == f"Voucher code: {code}"
    assert discount.name == voucher.name
    assert discount.type == DiscountType.VOUCHER
    assert discount.voucher_code == code
    # TODO (SHOPX-914): set translated voucher name
    assert discount.translated_name == ""

    assert order.base_shipping_price == shipping_price
    assert order.shipping_price_net == shipping_price
    assert order.shipping_price_gross == shipping_price * tax_rate
    assert order.subtotal_net_amount == subtotal.amount - discount_amount
    assert order.subtotal_gross_amount == (subtotal.amount - discount_amount) * tax_rate
    assert (
        order.total_net_amount
        == order.subtotal_net_amount + order.base_shipping_price_amount
    )
    assert (
        order.total_gross_amount
        == (order.subtotal_net_amount + order.base_shipping_price_amount) * tax_rate
    )
    assert order.undiscounted_total_net == subtotal + shipping_price
    assert order.undiscounted_total_gross == (subtotal + shipping_price) * tax_rate

    remaining_discount = discount_amount
    for idx, line in enumerate(lines):
        line.refresh_from_db()
        idx = variant_list.index(line.variant)
        base_price = unit_prices[idx]
        line_base_total = base_price
        if idx < len(lines) - 1:
            line_order_discount_portion = quantize_price(
                discount_amount * line_base_total / subtotal.amount, currency
            )
            remaining_discount -= line_order_discount_portion
        else:
            line_order_discount_portion = remaining_discount

        line_total_net_amount = (
            line.undiscounted_total_price_net_amount - line_order_discount_portion
        )
        assert line.undiscounted_total_price_net_amount == base_price
        assert line.undiscounted_unit_price_net_amount == base_price
        assert line.total_price_net_amount == line_total_net_amount
        assert line.base_unit_price_amount == base_price
        assert line.unit_price_net_amount == line_total_net_amount


def test_create_discount_for_voucher_entire_order_percentage(
    order_with_lines,
    voucher,
    plugins_manager,
    tax_configuration_flat_rates,
):
    # given
    assert voucher.type == VoucherType.ENTIRE_ORDER
    voucher.discount_value_type = DiscountValueType.PERCENTAGE
    voucher.save(update_fields=["discount_value_type"])

    order = order_with_lines
    order.status = OrderStatus.UNCONFIRMED
    tax_rate = Decimal("1.23")

    voucher_listing = voucher.channel_listings.get(channel=order.channel)
    discount_value = Decimal("50")
    voucher_listing.discount_value = discount_value
    voucher_listing.save(update_fields=["discount_value"])

    voucher.name = "Voucher name"
    voucher.save(update_fields=["name"])

    order.voucher = voucher
    code = voucher.codes.first().code
    order.voucher_code = code

    shipping_price = order.shipping_price.net
    currency = order.currency
    subtotal = zero_money(currency)
    lines = order.lines.all()
    for line in lines:
        subtotal += line.base_unit_price * line.quantity

    # when
    create_or_update_voucher_discount_objects_for_order(order)
    order, lines = fetch_order_prices_if_expired(order, plugins_manager, None, True)

    # then
    assert OrderDiscount.objects.count() == 1
    discount = order.discounts.first()
    assert discount.voucher == voucher
    assert discount.value_type == voucher.discount_value_type
    assert discount.value == discount_value
    assert discount.amount_value == Decimal(subtotal.amount / 2)
    assert discount.reason == f"Voucher code: {code}"
    assert discount.name == voucher.name
    assert discount.type == DiscountType.VOUCHER
    assert discount.voucher_code == code
    # TODO (SHOPX-914): set translated voucher name
    assert discount.translated_name == ""

    assert order.base_shipping_price == shipping_price
    assert order.shipping_price_net == shipping_price
    assert order.shipping_price_gross == shipping_price * tax_rate
    assert order.subtotal_net_amount == Decimal(subtotal.amount / 2)
    assert order.subtotal_gross_amount == Decimal(subtotal.amount / 2) * tax_rate
    assert (
        order.total_net_amount
        == order.subtotal_net_amount + order.base_shipping_price_amount
    )
    assert (
        order.total_gross_amount
        == (order.subtotal_net_amount + order.base_shipping_price_amount) * tax_rate
    )
    assert order.undiscounted_total_net == subtotal + shipping_price
    assert order.undiscounted_total_gross == (subtotal + shipping_price) * tax_rate

    lines = order.lines.all()
    line_1 = [line for line in lines if line.quantity == 3][0]
    line_2 = [line for line in lines if line.quantity == 2][0]

    variant_1 = line_1.variant
    variant_1_listing = variant_1.channel_listings.get(channel=order.channel)
    variant_1_undiscounted_unit_price = variant_1_listing.price_amount
    line_1_total_net_amount = quantize_price(
        line_1.undiscounted_total_price_net_amount / 2,
        currency,
    )
    assert (
        line_1.undiscounted_total_price_net_amount
        == variant_1_undiscounted_unit_price * line_1.quantity
    )
    assert (
        line_1.undiscounted_unit_price_net_amount == variant_1_undiscounted_unit_price
    )
    assert line_1.total_price_net_amount == line_1_total_net_amount
    assert line_1.base_unit_price_amount == variant_1_undiscounted_unit_price
    assert line_1.unit_price_net_amount == line_1_total_net_amount / line_1.quantity

    variant_2 = line_2.variant
    variant_2_listing = variant_2.channel_listings.get(channel=order.channel)
    variant_2_undiscounted_unit_price = variant_2_listing.price_amount
    line_2_total_net_amount = quantize_price(
        line_2.undiscounted_total_price_net_amount / 2,
        currency,
    )
    assert (
        line_2.undiscounted_total_price_net_amount
        == variant_2_undiscounted_unit_price * line_2.quantity
    )
    assert (
        line_2.undiscounted_unit_price_net_amount == variant_2_undiscounted_unit_price
    )
    assert line_2.total_price_net_amount == line_2_total_net_amount
    assert line_2.base_unit_price_amount == variant_2_undiscounted_unit_price
    assert line_2.unit_price_net_amount == line_2_total_net_amount / line_2.quantity


def test_create_discount_for_voucher_shipping_fixed(
    order_with_lines,
    voucher,
    plugins_manager,
    tax_configuration_flat_rates,
):
    # given
    voucher.type = VoucherType.SHIPPING
    voucher.discount_value_type = DiscountValueType.FIXED
    voucher.save(update_fields=["type", "discount_value_type"])

    order = order_with_lines
    order.status = OrderStatus.UNCONFIRMED
    tax_rate = Decimal("1.23")

    voucher_listing = voucher.channel_listings.get(channel=order.channel)
    discount_value = Decimal("5")
    voucher_listing.discount_value = discount_value
    voucher_listing.save(update_fields=["discount_value"])

    voucher.name = "Voucher shipping"
    voucher.save(update_fields=["name"])

    order.voucher = voucher
    code = voucher.codes.first().code
    order.voucher_code = code

    undiscounted_shipping_price = order.shipping_price.net.amount
    expected_shipping_price = Decimal(undiscounted_shipping_price - discount_value)
    currency = order.currency
    subtotal = zero_money(currency)
    lines = order.lines.all()
    for line in lines:
        subtotal += line.base_unit_price * line.quantity

    # when
    create_or_update_voucher_discount_objects_for_order(order)
    order, lines = fetch_order_prices_if_expired(order, plugins_manager, None, True)

    # then
    assert OrderDiscount.objects.count() == 1
    discount = order.discounts.first()
    assert discount.voucher == voucher
    assert discount.value_type == voucher.discount_value_type
    assert discount.value == discount_value
    assert (
        discount.amount_value == undiscounted_shipping_price - expected_shipping_price
    )
    assert discount.reason == f"Voucher code: {code}"
    assert discount.name == voucher.name
    assert discount.type == DiscountType.VOUCHER
    assert discount.voucher_code == code
    # TODO (SHOPX-914): set translated voucher name
    assert discount.translated_name == ""

    assert order.undiscounted_base_shipping_price_amount == undiscounted_shipping_price
    assert order.base_shipping_price_amount == expected_shipping_price
    assert order.shipping_price_net_amount == expected_shipping_price
    assert order.shipping_price_gross.amount == expected_shipping_price * tax_rate
    assert order.subtotal_net_amount == subtotal.amount
    assert order.subtotal_gross_amount == subtotal.amount * tax_rate
    assert order.total_net_amount == order.subtotal_net_amount + expected_shipping_price
    assert (
        order.total_gross_amount
        == (order.subtotal_net_amount + expected_shipping_price) * tax_rate
    )
    assert (
        order.undiscounted_total_net_amount
        == subtotal.amount + undiscounted_shipping_price
    )
    assert (
        order.undiscounted_total_gross_amount
        == (subtotal.amount + undiscounted_shipping_price) * tax_rate
    )


def test_create_discount_for_voucher_shipping_percentage(
    order_with_lines,
    voucher,
    plugins_manager,
    tax_configuration_flat_rates,
):
    # given
    voucher.type = VoucherType.SHIPPING
    voucher.discount_value_type = DiscountValueType.PERCENTAGE
    voucher.save(update_fields=["type", "discount_value_type"])

    order = order_with_lines
    order.status = OrderStatus.UNCONFIRMED
    tax_rate = Decimal("1.23")

    voucher_listing = voucher.channel_listings.get(channel=order.channel)
    discount_value = Decimal("50")
    voucher_listing.discount_value = discount_value
    voucher_listing.save(update_fields=["discount_value"])

    voucher.name = "Voucher shipping"
    voucher.save(update_fields=["name"])

    order.voucher = voucher
    code = voucher.codes.first().code
    order.voucher_code = code

    undiscounted_shipping_price = order.shipping_price.net.amount
    expected_shipping_price = Decimal(undiscounted_shipping_price / 2)
    currency = order.currency
    subtotal = zero_money(currency)
    lines = order.lines.all()
    for line in lines:
        subtotal += line.base_unit_price * line.quantity

    # when
    create_or_update_voucher_discount_objects_for_order(order)
    order, lines = fetch_order_prices_if_expired(order, plugins_manager, None, True)

    # then
    assert OrderDiscount.objects.count() == 1
    discount = order.discounts.first()
    assert discount.voucher == voucher
    assert discount.value_type == voucher.discount_value_type
    assert discount.value == discount_value
    assert (
        discount.amount_value == undiscounted_shipping_price - expected_shipping_price
    )
    assert discount.reason == f"Voucher code: {code}"
    assert discount.name == voucher.name
    assert discount.type == DiscountType.VOUCHER
    assert discount.voucher_code == code
    # TODO (SHOPX-914): set translated voucher name
    assert discount.translated_name == ""

    assert order.undiscounted_base_shipping_price.amount == undiscounted_shipping_price
    assert order.base_shipping_price.amount == expected_shipping_price
    assert order.shipping_price_net_amount == expected_shipping_price
    assert order.shipping_price_gross.amount == expected_shipping_price * tax_rate
    assert order.subtotal_net_amount == subtotal.amount
    assert order.subtotal_gross_amount == subtotal.amount * tax_rate
    assert order.total_net_amount == order.subtotal_net_amount + expected_shipping_price
    assert (
        order.total_gross_amount
        == (order.subtotal_net_amount + expected_shipping_price) * tax_rate
    )
    assert (
        order.undiscounted_total_net_amount
        == subtotal.amount + undiscounted_shipping_price
    )
    assert (
        order.undiscounted_total_gross_amount
        == (subtotal.amount + undiscounted_shipping_price) * tax_rate
    )


def test_create_discount_for_voucher_specific_product_line_with_catalogue_discount(
    order_with_lines_and_catalogue_promotion,
    plugins_manager,
    tax_configuration_flat_rates,
    voucher_specific_product_type,
):
    # given
    order = order_with_lines_and_catalogue_promotion
    currency = order.currency
    order.status = OrderStatus.UNCONFIRMED
    channel = order.channel
    rule = PromotionRule.objects.get()
    promotion_id = graphene.Node.to_global_id("Promotion", rule.promotion_id)
    catalogue_reward_value = rule.reward_value
    catalogue_reward_value_type = rule.reward_value_type
    assert catalogue_reward_value_type == DiscountValueType.FIXED

    line_1, line_2 = order.lines.all()
    voucher = voucher_specific_product_type
    voucher.products.set([])
    voucher.variants.set([line_1.variant])
    voucher_listing = voucher.channel_listings.get(channel=channel)
    voucher_reward_value = voucher_listing.discount_value
    voucher_reward_value_type = voucher.discount_value_type
    assert voucher_reward_value_type == DiscountValueType.PERCENTAGE
    order.voucher_code = voucher.codes.first().code
    order.voucher = voucher
    order.save(update_fields=["voucher_code", "voucher"])

    tax_rate = Decimal("1.23")

    # when
    create_or_update_voucher_discount_objects_for_order(order)
    order, lines = fetch_order_prices_if_expired(order, plugins_manager, None, True)

    # then
    assert OrderLineDiscount.objects.count() == 2
    assert not OrderDiscount.objects.exists()

    line_1, line_2 = lines
    catalogue_discount = line_1.discounts.get(type=DiscountType.PROMOTION)
    catalogue_unit_discount_amount = catalogue_reward_value
    catalogue_discount_amount = catalogue_unit_discount_amount * line_1.quantity
    assert catalogue_discount.amount_value == catalogue_discount_amount
    assert catalogue_discount.value == catalogue_reward_value
    assert catalogue_discount.value_type == catalogue_reward_value_type
    assert catalogue_discount.type == DiscountType.PROMOTION
    assert catalogue_discount.reason == f"Promotion: {promotion_id}"

    voucher_discount = line_1.discounts.get(type=DiscountType.VOUCHER)
    voucher_unit_discount_amount = (
        voucher_reward_value
        / 100
        * (line_1.undiscounted_base_unit_price_amount - catalogue_unit_discount_amount)
    )
    voucher_discount_amount = voucher_unit_discount_amount * line_1.quantity
    assert voucher_discount.amount_value == voucher_discount_amount
    assert voucher_discount.value == voucher_reward_value
    assert voucher_discount.value_type == voucher_reward_value_type
    assert voucher_discount.type == DiscountType.VOUCHER
    assert voucher_discount.reason == f"Voucher code: {order.voucher_code}"

    variant_1 = line_1.variant
    variant_1_listing = variant_1.channel_listings.get(channel=channel)
    variant_1_undiscounted_unit_price = variant_1_listing.price_amount
    assert (
        line_1.undiscounted_base_unit_price_amount == variant_1_undiscounted_unit_price
    )

    assert (
        line_1.undiscounted_total_price_net_amount
        == variant_1_undiscounted_unit_price * line_1.quantity
    )
    assert (
        line_1.undiscounted_total_price_gross_amount
        == line_1.undiscounted_total_price_net_amount * tax_rate
    )
    assert (
        line_1.undiscounted_unit_price_net_amount == variant_1_undiscounted_unit_price
    )
    assert (
        line_1.undiscounted_unit_price_gross_amount
        == variant_1_undiscounted_unit_price * tax_rate
    )

    line_1_base_unit_price = (
        variant_1_undiscounted_unit_price
        - catalogue_unit_discount_amount
        - voucher_unit_discount_amount
    )
    assert line_1.base_unit_price_amount == line_1_base_unit_price
    assert line_1.unit_price_net_amount == line_1_base_unit_price
    assert line_1.unit_price_gross_amount == quantize_price(
        line_1_base_unit_price * tax_rate, currency
    )
    assert (
        line_1.total_price_net_amount == line_1.unit_price_net_amount * line_1.quantity
    )
    assert line_1.total_price_gross_amount == quantize_price(
        line_1.total_price_net_amount * tax_rate, currency
    )

    variant_2 = line_2.variant
    variant_2_listing = variant_2.channel_listings.get(channel=channel)
    variant_2_undiscounted_unit_price = variant_2_listing.price_amount
    assert (
        line_2.undiscounted_total_price_net_amount
        == variant_2_undiscounted_unit_price * line_2.quantity
    )
    assert (
        line_2.undiscounted_total_price_gross_amount
        == line_2.undiscounted_total_price_net_amount * tax_rate
    )
    assert (
        line_2.undiscounted_unit_price_net_amount == variant_2_undiscounted_unit_price
    )
    assert (
        line_2.undiscounted_unit_price_gross_amount
        == variant_2_undiscounted_unit_price * tax_rate
    )
    assert line_2.base_unit_price_amount == variant_2_undiscounted_unit_price
    assert line_2.unit_price_net_amount == variant_2_undiscounted_unit_price
    assert (
        line_2.unit_price_gross_amount == variant_2_undiscounted_unit_price * tax_rate
    )
    assert line_2.total_price_net_amount == line_2.undiscounted_total_price_net_amount
    assert (
        line_2.total_price_gross_amount == line_2.undiscounted_total_price_gross_amount
    )

    shipping_net_price = order.shipping_price_net_amount
    assert (
        order.undiscounted_total_net_amount
        == line_1.undiscounted_total_price_net_amount
        + line_2.undiscounted_total_price_net_amount
        + shipping_net_price
    )
    assert (
        order.undiscounted_total_gross_amount
        == order.undiscounted_total_net_amount * tax_rate
    )
    assert (
        order.total_net_amount
        == order.undiscounted_total_net_amount
        - catalogue_discount_amount
        - voucher_discount_amount
    )
    assert order.total_gross_amount == quantize_price(
        order.total_net_amount * tax_rate, currency
    )
    assert order.subtotal_net_amount == order.total_net_amount - shipping_net_price
    assert order.subtotal_gross_amount == quantize_price(
        order.subtotal_net_amount * tax_rate, currency
    )

    assert (
        line_1.unit_discount_amount
        == catalogue_unit_discount_amount + voucher_unit_discount_amount
    )
    assert (
        line_1.unit_discount_reason
        == f"Promotion: {promotion_id}; Voucher code: {order.voucher_code}"
    )
