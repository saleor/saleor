from decimal import Decimal

import pytest
from prices import Money

from ....core.prices import quantize_price
from ....core.taxes import zero_money
from ....order import OrderStatus
from ....order.calculations import fetch_order_prices_if_expired
from ... import DiscountType, DiscountValueType, VoucherType
from ...models import OrderDiscount, OrderLineDiscount, Voucher
from ...utils.voucher import create_or_update_voucher_discount_objects_for_order


def test_update_voucher_discount_specific_product_with_different_variants(
    order_with_lines,
    plugins_manager,
    tax_configuration_flat_rates,
    voucher_list,
):
    # given
    order = order_with_lines
    order.status = OrderStatus.UNCONFIRMED
    tax_rate = Decimal("1.23")

    lines = order.lines.all()
    line_1, line_2 = lines
    shipping_price = order.shipping_price.net
    currency = order.currency
    undiscounted_subtotal = zero_money(currency)
    for line in lines:
        undiscounted_subtotal += line.undiscounted_base_unit_price * line.quantity

    # prepare vouchers
    voucher_1, voucher_2, _ = voucher_list
    for voucher in voucher_list:
        voucher.discount_value_type = DiscountValueType.FIXED
        voucher.type = VoucherType.SPECIFIC_PRODUCT
    Voucher.objects.bulk_update(voucher_list, ["discount_value_type", "type"])
    voucher_1.variants.add(line_1.variant)
    voucher_2.variants.add(line_2.variant)

    # apply specific product voucher for line_1 variant
    voucher_listing_1 = voucher_1.channel_listings.get(channel=order.channel)
    voucher_1_unit_discount_amount = voucher_listing_1.discount_value
    order.voucher = voucher_1
    order.voucher_code = voucher_1.codes.first().code
    create_or_update_voucher_discount_objects_for_order(order)
    order, lines = fetch_order_prices_if_expired(order, plugins_manager, None, True)

    line_1, line_2 = lines
    discount_1 = line_1.discounts.get()
    discount_amount_1 = voucher_1_unit_discount_amount * line_1.quantity
    assert (
        line_1.base_unit_price_amount
        == line_1.undiscounted_base_unit_price_amount - voucher_1_unit_discount_amount
    )
    assert discount_1.value == voucher_1_unit_discount_amount
    assert discount_1.amount_value == discount_amount_1

    # apply specific product voucher for line_2 variant
    voucher_listing_2 = voucher_2.channel_listings.get(channel=order.channel)
    voucher_2_unit_discount_amount = voucher_listing_2.discount_value
    order.voucher = voucher_2
    order.voucher_code = voucher_2.codes.first().code
    assert voucher_2_unit_discount_amount != voucher_1_unit_discount_amount

    # when
    create_or_update_voucher_discount_objects_for_order(order)
    order, lines = fetch_order_prices_if_expired(order, plugins_manager, None, True)

    # then
    line_1, line_2 = lines

    with pytest.raises(OrderLineDiscount.DoesNotExist):
        discount_1.refresh_from_db()

    assert line_1.base_unit_price_amount == line_1.undiscounted_base_unit_price_amount
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

    discount_2 = line_2.discounts.get()
    discount_amount_2 = voucher_2_unit_discount_amount * line_2.quantity
    assert discount_2.amount_value == discount_amount_2
    assert discount_2.value_type == DiscountValueType.FIXED
    assert discount_2.type == DiscountType.VOUCHER
    assert discount_2.reason == f"Voucher code: {order.voucher_code}"
    assert discount_2.value == voucher_2_unit_discount_amount

    assert (
        line_2.base_unit_price_amount
        == line_2.undiscounted_base_unit_price_amount - voucher_2_unit_discount_amount
    )
    assert (
        line_2.total_price_gross_amount
        == line_2.base_unit_price_amount * line_2.quantity * tax_rate
    )
    assert (
        line_2.undiscounted_total_price_gross_amount
        == line_2.undiscounted_base_unit_price_amount * line_2.quantity * tax_rate
    )
    assert line_2.unit_discount_amount == voucher_2_unit_discount_amount
    assert line_2.unit_discount_type == DiscountValueType.FIXED
    assert line_2.unit_discount_reason == f"Voucher code: {order.voucher_code}"

    assert order.base_shipping_price == shipping_price
    assert order.shipping_price_net == shipping_price
    assert order.shipping_price_gross == shipping_price * tax_rate
    assert order.subtotal_net_amount == undiscounted_subtotal.amount - discount_amount_2
    assert (
        order.subtotal_gross_amount
        == (undiscounted_subtotal.amount - discount_amount_2) * tax_rate
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


def test_update_voucher_discount_specific_product_with_apply_once_per_order(
    order_with_lines,
    plugins_manager,
    tax_configuration_flat_rates,
    voucher_list,
):
    # given
    order = order_with_lines
    order.status = OrderStatus.UNCONFIRMED
    tax_rate = Decimal("1.23")

    lines = order.lines.all()
    cheapest_line, line_2 = lines
    assert cheapest_line.base_unit_price_amount < line_2.base_unit_price_amount
    shipping_price = order.shipping_price.net
    currency = order.currency
    undiscounted_subtotal = zero_money(currency)
    for line in lines:
        undiscounted_subtotal += line.undiscounted_base_unit_price * line.quantity

    # prepare vouchers
    voucher_1, voucher_2, _ = voucher_list
    voucher_1.discount_value_type = DiscountValueType.FIXED
    voucher_1.type = VoucherType.SPECIFIC_PRODUCT
    voucher_1.variants.add(line_2.variant)
    voucher_2.discount_value_type = DiscountValueType.FIXED
    voucher_2.type = VoucherType.ENTIRE_ORDER
    voucher_2.apply_once_per_order = True
    Voucher.objects.bulk_update(
        [voucher_1, voucher_2], ["discount_value_type", "type", "apply_once_per_order"]
    )

    # apply specific product voucher for line_2 variant
    voucher_listing_1 = voucher_1.channel_listings.get(channel=order.channel)
    voucher_1_unit_discount_amount = voucher_listing_1.discount_value
    order.voucher = voucher_1
    order.voucher_code = voucher_1.codes.first().code
    create_or_update_voucher_discount_objects_for_order(order)
    order, lines = fetch_order_prices_if_expired(order, plugins_manager, None, True)

    cheapest_line, line_2 = lines
    discount_1 = line_2.discounts.get()
    discount_amount_1 = voucher_1_unit_discount_amount * line_2.quantity
    assert (
        line_2.base_unit_price_amount
        == line_2.undiscounted_base_unit_price_amount - voucher_1_unit_discount_amount
    )
    assert discount_1.value == voucher_1_unit_discount_amount
    assert discount_1.amount_value == discount_amount_1
    assert not cheapest_line.discounts.exists()

    # apply voucher apply once per order type
    voucher_listing_2 = voucher_2.channel_listings.get(channel=order.channel)
    voucher_2_discount_amount = voucher_listing_2.discount_value
    order.voucher = voucher_2
    order.voucher_code = voucher_2.codes.first().code

    # when
    create_or_update_voucher_discount_objects_for_order(order)
    order, lines = fetch_order_prices_if_expired(order, plugins_manager, None, True)

    # then
    cheapest_line, line_2 = lines
    with pytest.raises(OrderLineDiscount.DoesNotExist):
        discount_1.refresh_from_db()

    assert line_2.base_unit_price_amount == line_2.undiscounted_base_unit_price_amount
    assert (
        line_2.total_price_gross_amount
        == line_2.undiscounted_base_unit_price_amount * line_2.quantity * tax_rate
    )
    assert (
        line_2.undiscounted_total_price_gross_amount
        == line_2.undiscounted_base_unit_price_amount * line_2.quantity * tax_rate
    )
    assert line_2.unit_discount_amount == 0
    assert line_2.unit_discount_type is None
    assert line_2.unit_discount_reason is None
    assert line_2.unit_discount_value == 0

    discount_2 = cheapest_line.discounts.get()
    discount_amount_2 = voucher_2_discount_amount
    assert discount_2.amount_value == discount_amount_2
    assert discount_2.value_type == DiscountValueType.FIXED
    assert discount_2.type == DiscountType.VOUCHER
    assert discount_2.reason == f"Voucher code: {order.voucher_code}"
    assert discount_2.value == voucher_2_discount_amount

    unit_discount_amount_2 = discount_amount_2 / cheapest_line.quantity
    assert quantize_price(
        cheapest_line.base_unit_price_amount, currency
    ) == quantize_price(
        cheapest_line.undiscounted_base_unit_price_amount - unit_discount_amount_2,
        currency,
    )
    assert cheapest_line.total_price_gross_amount == quantize_price(
        cheapest_line.base_unit_price_amount * cheapest_line.quantity * tax_rate,
        currency,
    )
    assert (
        cheapest_line.undiscounted_total_price_gross_amount
        == cheapest_line.undiscounted_base_unit_price_amount
        * cheapest_line.quantity
        * tax_rate
    )
    assert cheapest_line.unit_discount_amount == unit_discount_amount_2
    assert cheapest_line.unit_discount_type == DiscountValueType.FIXED
    assert cheapest_line.unit_discount_reason == f"Voucher code: {order.voucher_code}"

    assert order.base_shipping_price == shipping_price
    assert order.shipping_price_net == shipping_price
    assert order.shipping_price_gross == shipping_price * tax_rate
    assert order.subtotal_net_amount == undiscounted_subtotal.amount - discount_amount_2
    assert (
        order.subtotal_gross_amount
        == (undiscounted_subtotal.amount - discount_amount_2) * tax_rate
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


def test_update_voucher_discount_apply_once_per_order_with_specific_product(
    order_with_lines,
    plugins_manager,
    tax_configuration_flat_rates,
    voucher_list,
):
    # given
    order = order_with_lines
    order.status = OrderStatus.UNCONFIRMED
    tax_rate = Decimal("1.23")

    lines = order.lines.all()
    line_1, line_2 = lines
    assert line_1.base_unit_price_amount < line_2.base_unit_price_amount
    shipping_price = order.shipping_price.net
    currency = order.currency
    undiscounted_subtotal = zero_money(currency)
    for line in lines:
        undiscounted_subtotal += line.undiscounted_base_unit_price * line.quantity

    # prepare vouchers
    voucher_1, voucher_2, _ = voucher_list
    voucher_1.discount_value_type = DiscountValueType.FIXED
    voucher_1.type = VoucherType.ENTIRE_ORDER
    voucher_1.apply_once_per_order = True
    voucher_2.type = VoucherType.SPECIFIC_PRODUCT
    voucher_2.discount_value_type = DiscountValueType.PERCENTAGE
    voucher_2.variants.add(line_1.variant)
    Voucher.objects.bulk_update(
        [voucher_1, voucher_2], ["discount_value_type", "type", "apply_once_per_order"]
    )

    # apply voucher apply once per order type
    voucher_listing_1 = voucher_1.channel_listings.get(channel=order.channel)
    voucher_1_discount_amount = voucher_listing_1.discount_value
    voucher_1_unit_discount_amount = voucher_1_discount_amount / line_1.quantity
    order.voucher = voucher_1
    order.voucher_code = voucher_1.codes.first().code
    create_or_update_voucher_discount_objects_for_order(order)
    order, lines = fetch_order_prices_if_expired(order, plugins_manager, None, True)

    line_1, line_2 = lines
    discount = line_1.discounts.get()
    assert quantize_price(line_1.base_unit_price_amount, currency) == quantize_price(
        line_1.undiscounted_base_unit_price_amount - voucher_1_unit_discount_amount,
        currency,
    )
    assert discount.value == voucher_1_discount_amount
    assert discount.amount_value == voucher_1_discount_amount
    assert not line_2.discounts.exists()

    # apply specific product voucher for line 1 variant
    voucher_listing_2 = voucher_2.channel_listings.get(channel=order.channel)
    voucher_2_discount_value = Decimal("20")
    voucher_listing_2.discount_value = voucher_2_discount_value
    voucher_listing_2.save(update_fields=["discount_value"])
    order.voucher = voucher_2
    order.voucher_code = voucher_2.codes.first().code

    # when
    create_or_update_voucher_discount_objects_for_order(order)
    order, lines = fetch_order_prices_if_expired(order, plugins_manager, None, True)

    # then
    line_1, line_2 = lines

    assert (
        line_1.base_unit_price_amount
        == line_1.undiscounted_base_unit_price_amount
        * (100 - voucher_2_discount_value)
        / 100
    )
    assert (
        line_1.total_price_gross_amount
        == line_1.base_unit_price_amount * line_1.quantity * tax_rate
    )
    assert (
        line_1.undiscounted_total_price_gross_amount
        == line_1.undiscounted_base_unit_price_amount * line_1.quantity * tax_rate
    )
    assert (
        line_1.unit_discount_amount
        == line_1.undiscounted_base_unit_price_amount - line_1.base_unit_price_amount
    )
    assert (
        line_1.unit_discount_type
        == DiscountValueType.PERCENTAGE
        == voucher_2.discount_value_type
    )
    assert line_1.unit_discount_reason == f"Voucher code: {order.voucher_code}"

    discount.refresh_from_db()
    assert discount.amount_value == line_1.unit_discount_amount * line_1.quantity
    assert discount.value_type == DiscountValueType.PERCENTAGE
    assert discount.type == DiscountType.VOUCHER
    assert discount.reason == f"Voucher code: {order.voucher_code}"
    assert discount.value == voucher_2_discount_value

    assert order.base_shipping_price == shipping_price
    assert order.shipping_price_net == shipping_price
    assert order.shipping_price_gross == shipping_price * tax_rate
    assert (
        order.subtotal_net_amount
        == undiscounted_subtotal.amount - line_1.unit_discount_amount * line_1.quantity
    )
    assert order.subtotal_gross_amount == order.subtotal_net_amount * tax_rate
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


def test_update_voucher_discount_specific_product_with_entire_order(
    order_with_lines,
    plugins_manager,
    tax_configuration_flat_rates,
    voucher_list,
):
    # given
    order = order_with_lines
    order.status = OrderStatus.UNCONFIRMED
    tax_rate = Decimal("1.23")

    lines = order.lines.all()
    line_1, line_2 = lines
    shipping_price = order.shipping_price.net
    currency = order.currency
    undiscounted_subtotal = zero_money(currency)
    for line in lines:
        undiscounted_subtotal += line.undiscounted_base_unit_price * line.quantity

    # prepare vouchers
    voucher_1, voucher_2, _ = voucher_list
    voucher_1.discount_value_type = DiscountValueType.FIXED
    voucher_1.type = VoucherType.SPECIFIC_PRODUCT
    voucher_1.variants.add(line_2.variant)
    voucher_2.discount_value_type = DiscountValueType.FIXED
    voucher_2.type = VoucherType.ENTIRE_ORDER
    voucher_2.apply_once_per_order = False
    Voucher.objects.bulk_update(
        [voucher_1, voucher_2], ["discount_value_type", "type", "apply_once_per_order"]
    )

    # apply specific product voucher for line 2 variant
    voucher_listing_1 = voucher_1.channel_listings.get(channel=order.channel)
    voucher_1_unit_discount_amount = voucher_listing_1.discount_value
    order.voucher = voucher_1
    order.voucher_code = voucher_1.codes.first().code
    create_or_update_voucher_discount_objects_for_order(order)
    order, lines = fetch_order_prices_if_expired(order, plugins_manager, None, True)

    line_1, line_2 = lines
    discount_1 = line_2.discounts.get()
    discount_amount_1 = voucher_1_unit_discount_amount * line_2.quantity
    assert (
        line_2.base_unit_price_amount
        == line_2.undiscounted_base_unit_price_amount - voucher_1_unit_discount_amount
    )
    assert discount_1.value == voucher_1_unit_discount_amount
    assert discount_1.amount_value == discount_amount_1
    assert not line_1.discounts.exists()

    # apply entire order voucher
    voucher_listing_2 = voucher_2.channel_listings.get(channel=order.channel)
    voucher_2_discount_value = Decimal("20")
    voucher_listing_2.discount_value = voucher_2_discount_value
    voucher_listing_2.save(update_fields=["discount_value"])
    order.voucher = voucher_2
    order.voucher_code = voucher_2.codes.first().code

    # when
    create_or_update_voucher_discount_objects_for_order(order)
    order, lines = fetch_order_prices_if_expired(order, plugins_manager, None, True)

    # then
    with pytest.raises(OrderLineDiscount.DoesNotExist):
        discount_1.refresh_from_db()

    discount_2 = order.discounts.get()
    assert discount_2.amount_value == voucher_2_discount_value
    assert discount_2.value_type == DiscountValueType.FIXED
    assert discount_2.type == DiscountType.VOUCHER
    assert discount_2.reason == f"Voucher code: {order.voucher_code}"
    assert discount_2.value == voucher_2_discount_value

    assert order.base_shipping_price == shipping_price
    assert order.shipping_price_net == shipping_price
    assert order.shipping_price_gross == shipping_price * tax_rate
    assert (
        order.subtotal_net_amount
        == undiscounted_subtotal.amount - voucher_2_discount_value
    )
    assert (
        order.subtotal_gross_amount
        == (undiscounted_subtotal.amount - voucher_2_discount_value) * tax_rate
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

    line_1, line_2 = lines
    assert line_1.base_unit_price_amount == line_1.undiscounted_base_unit_price_amount
    assert line_2.base_unit_price_amount == line_2.undiscounted_base_unit_price_amount

    line_1_total_base_price = line_1.base_unit_price_amount * line_1.quantity
    line_2_total_base_price = line_2.base_unit_price_amount * line_2.quantity
    base_subtotal = line_1_total_base_price + line_2_total_base_price
    line_1_discount_portion = (
        line_1_total_base_price / base_subtotal * voucher_2_discount_value
    )
    line_2_discount_portion = voucher_2_discount_value - line_1_discount_portion

    assert line_1.total_price_net_amount == quantize_price(
        line_1_total_base_price - line_1_discount_portion, currency
    )
    assert line_1.total_price_gross_amount == quantize_price(
        line_1.total_price_net_amount * tax_rate, currency
    )
    assert (
        line_1.undiscounted_total_price_net_amount
        == line_1.undiscounted_base_unit_price_amount * line_1.quantity
    )
    assert (
        line_1.undiscounted_total_price_gross_amount
        == line_1.undiscounted_total_price_net_amount * tax_rate
    )

    assert line_1.unit_discount_amount == 0
    assert line_1.unit_discount_value == 0
    assert line_1.unit_discount_type is None
    assert line_1.unit_discount_reason is None
    assert not line_1.discounts.exists()

    assert line_2.total_price_net_amount == quantize_price(
        line_2_total_base_price - line_2_discount_portion, currency
    )
    assert line_2.total_price_gross_amount == quantize_price(
        line_2.total_price_net_amount * tax_rate, currency
    )
    assert (
        line_2.undiscounted_total_price_net_amount
        == line_2.undiscounted_base_unit_price_amount * line_2.quantity
    )
    assert (
        line_2.undiscounted_total_price_gross_amount
        == line_2.undiscounted_total_price_net_amount * tax_rate
    )

    assert line_2.unit_discount_amount == 0
    assert line_2.unit_discount_value == 0
    assert line_2.unit_discount_type is None
    assert line_2.unit_discount_reason is None
    assert not line_2.discounts.exists()


def test_update_voucher_discount_shipping_with_specific_product(
    order_with_lines,
    plugins_manager,
    tax_configuration_flat_rates,
    voucher_list,
):
    # given
    order = order_with_lines
    order.status = OrderStatus.UNCONFIRMED
    tax_rate = Decimal("1.23")

    lines = order.lines.all()
    line_1, line_2 = lines
    undiscounted_shipping_price = order.undiscounted_base_shipping_price
    currency = order.currency
    undiscounted_subtotal = zero_money(currency)
    for line in lines:
        undiscounted_subtotal += line.undiscounted_base_unit_price * line.quantity

    # prepare vouchers
    voucher_1, voucher_2, _ = voucher_list
    voucher_1.discount_value_type = DiscountValueType.FIXED
    voucher_1.type = VoucherType.SHIPPING
    voucher_2.discount_value_type = DiscountValueType.FIXED
    voucher_2.type = VoucherType.SPECIFIC_PRODUCT
    voucher_2.variants.add(line_1.variant)
    Voucher.objects.bulk_update([voucher_1, voucher_2], ["discount_value_type", "type"])

    # apply shipping voucher
    voucher_listing_1 = voucher_1.channel_listings.get(channel=order.channel)
    voucher_1_discount = Money(voucher_listing_1.discount_value, currency)
    shipping_price_after_discount = undiscounted_shipping_price - voucher_1_discount
    order.voucher = voucher_1
    order.voucher_code = voucher_1.codes.first().code
    create_or_update_voucher_discount_objects_for_order(order)
    order, lines = fetch_order_prices_if_expired(order, plugins_manager, None, True)

    assert order.undiscounted_base_shipping_price == undiscounted_shipping_price
    assert order.base_shipping_price == shipping_price_after_discount
    assert order.shipping_price_net == shipping_price_after_discount
    assert order.shipping_price_gross == quantize_price(
        shipping_price_after_discount * tax_rate, currency
    )
    shipping_discount = order.discounts.get()
    assert shipping_discount.amount == voucher_1_discount

    # apply specific product voucher for line 1 variant
    voucher_listing_2 = voucher_2.channel_listings.get(channel=order.channel)
    voucher_2_unit_discount = voucher_listing_2.discount_value
    order.voucher = voucher_2
    order.voucher_code = voucher_2.codes.first().code

    # when
    create_or_update_voucher_discount_objects_for_order(order)
    order, lines = fetch_order_prices_if_expired(order, plugins_manager, None, True)

    # then
    line_1, line_2 = lines

    discount_2 = line_1.discounts.get()
    discount_amount_2 = voucher_2_unit_discount * line_1.quantity
    assert discount_2.amount_value == discount_amount_2
    assert discount_2.value_type == voucher_2.discount_value_type
    assert discount_2.type == DiscountType.VOUCHER
    assert discount_2.reason == f"Voucher code: {order.voucher_code}"
    assert discount_2.value == voucher_2_unit_discount

    assert quantize_price(line_1.base_unit_price_amount, currency) == quantize_price(
        line_1.undiscounted_base_unit_price_amount - voucher_2_unit_discount,
        currency,
    )
    assert line_1.total_price_gross_amount == quantize_price(
        line_1.base_unit_price_amount * line_1.quantity * tax_rate,
        currency,
    )
    assert (
        line_1.undiscounted_total_price_gross_amount
        == line_1.undiscounted_base_unit_price_amount * line_1.quantity * tax_rate
    )
    assert line_1.unit_discount_amount == voucher_2_unit_discount
    assert line_1.unit_discount_type == voucher_2.discount_value_type
    assert line_1.unit_discount_reason == f"Voucher code: {order.voucher_code}"
    assert line_1.unit_discount_value == voucher_2_unit_discount

    assert line_2.base_unit_price_amount == line_2.undiscounted_base_unit_price_amount
    assert (
        line_2.total_price_gross_amount
        == line_2.undiscounted_base_unit_price_amount * line_2.quantity * tax_rate
    )
    assert (
        line_2.undiscounted_total_price_gross_amount
        == line_2.undiscounted_base_unit_price_amount * line_2.quantity * tax_rate
    )
    assert line_2.unit_discount_amount == 0
    assert line_2.unit_discount_type is None
    assert line_2.unit_discount_reason is None
    assert line_2.unit_discount_value == 0

    with pytest.raises(OrderDiscount.DoesNotExist):
        shipping_discount.refresh_from_db()
    assert not order.discounts.exists()

    assert order.base_shipping_price == undiscounted_shipping_price
    assert order.shipping_price_net == undiscounted_shipping_price
    assert order.shipping_price_gross == undiscounted_shipping_price * tax_rate
    assert order.subtotal_net_amount == undiscounted_subtotal.amount - discount_amount_2
    assert (
        order.subtotal_gross_amount
        == (undiscounted_subtotal.amount - discount_amount_2) * tax_rate
    )
    assert (
        order.total_net_amount
        == order.subtotal_net_amount + order.base_shipping_price_amount
    )
    assert (
        order.total_gross_amount
        == (order.subtotal_net_amount + order.base_shipping_price_amount) * tax_rate
    )
    assert (
        order.undiscounted_total_net
        == undiscounted_subtotal + undiscounted_shipping_price
    )
    assert (
        order.undiscounted_total_gross
        == (undiscounted_subtotal + undiscounted_shipping_price) * tax_rate
    )


def test_update_voucher_discount_specific_product_with_shipping(
    order_with_lines,
    plugins_manager,
    tax_configuration_flat_rates,
    voucher_list,
):
    # given
    order = order_with_lines
    order.status = OrderStatus.UNCONFIRMED
    tax_rate = Decimal("1.23")

    lines = order.lines.all()
    line_1, line_2 = lines
    undiscounted_shipping_price = order.undiscounted_base_shipping_price
    currency = order.currency
    undiscounted_subtotal = zero_money(currency)
    for line in lines:
        undiscounted_subtotal += line.undiscounted_base_unit_price * line.quantity

    # prepare vouchers
    voucher_1, voucher_2, _ = voucher_list
    voucher_1.discount_value_type = DiscountValueType.FIXED
    voucher_1.type = VoucherType.SPECIFIC_PRODUCT
    voucher_1.variants.add(line_1.variant)
    voucher_2.discount_value_type = DiscountValueType.FIXED
    voucher_2.type = VoucherType.SHIPPING
    Voucher.objects.bulk_update([voucher_1, voucher_2], ["discount_value_type", "type"])

    # apply specific product voucher for line 1 variant
    voucher_listing_1 = voucher_1.channel_listings.get(channel=order.channel)
    voucher_1_unit_discount = voucher_listing_1.discount_value
    order.voucher = voucher_1
    order.voucher_code = voucher_1.codes.first().code
    create_or_update_voucher_discount_objects_for_order(order)
    order, lines = fetch_order_prices_if_expired(order, plugins_manager, None, True)

    line_1, line_2 = lines
    assert (
        line_1.base_unit_price_amount
        == line_1.undiscounted_base_unit_price_amount - voucher_1_unit_discount
    )
    discount_1 = line_1.discounts.get()
    assert discount_1.amount_value == voucher_1_unit_discount * line_1.quantity

    # apply shipping voucher
    voucher_listing_2 = voucher_2.channel_listings.get(channel=order.channel)
    voucher_2_discount = Money(voucher_listing_2.discount_value, currency)
    shipping_price_after_discount = undiscounted_shipping_price - voucher_2_discount
    order.voucher = voucher_2
    order.voucher_code = voucher_2.codes.first().code

    # when
    create_or_update_voucher_discount_objects_for_order(order)
    order, lines = fetch_order_prices_if_expired(order, plugins_manager, None, True)

    # then
    line_1, line_2 = lines
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
    assert line_1.unit_discount_value == 0

    assert line_2.base_unit_price_amount == line_2.undiscounted_base_unit_price_amount
    assert (
        line_2.total_price_gross_amount
        == line_2.undiscounted_base_unit_price_amount * line_2.quantity * tax_rate
    )
    assert (
        line_2.undiscounted_total_price_gross_amount
        == line_2.undiscounted_base_unit_price_amount * line_2.quantity * tax_rate
    )
    assert line_2.unit_discount_amount == 0
    assert line_2.unit_discount_type is None
    assert line_2.unit_discount_reason is None
    assert line_2.unit_discount_value == 0

    with pytest.raises(OrderLineDiscount.DoesNotExist):
        discount_1.refresh_from_db()

    shipping_discount = order.discounts.get()
    assert shipping_discount.amount == voucher_2_discount
    assert shipping_discount.value_type == voucher_2.discount_value_type
    assert shipping_discount.type == DiscountType.VOUCHER
    assert shipping_discount.reason == f"Voucher code: {order.voucher_code}"
    assert shipping_discount.value == voucher_2_discount.amount

    assert order.undiscounted_base_shipping_price == undiscounted_shipping_price
    assert order.base_shipping_price == shipping_price_after_discount
    assert order.shipping_price_net == shipping_price_after_discount
    assert order.shipping_price_gross == quantize_price(
        shipping_price_after_discount * tax_rate, currency
    )

    assert (
        order.undiscounted_total_net
        == undiscounted_subtotal + undiscounted_shipping_price
    )
    assert (
        order.undiscounted_total_gross
        == (undiscounted_subtotal + undiscounted_shipping_price) * tax_rate
    )
    assert order.subtotal_net_amount == undiscounted_subtotal.amount
    assert order.subtotal_gross_amount == undiscounted_subtotal.amount * tax_rate
    assert (
        order.total_net_amount
        == order.subtotal_net_amount + order.base_shipping_price_amount
    )
    assert order.total_gross == quantize_price(
        (order.undiscounted_total_net - voucher_2_discount) * tax_rate, currency
    )


def test_update_voucher_discount_shipping_with_entire_order(
    order_with_lines,
    plugins_manager,
    tax_configuration_flat_rates,
    voucher_list,
):
    # given
    order = order_with_lines
    order.status = OrderStatus.UNCONFIRMED
    tax_rate = Decimal("1.23")

    lines = order.lines.all()
    undiscounted_shipping_price = order.undiscounted_base_shipping_price
    currency = order.currency
    undiscounted_subtotal = zero_money(currency)
    for line in lines:
        undiscounted_subtotal += line.undiscounted_base_unit_price * line.quantity

    # prepare vouchers
    voucher_1, voucher_2, _ = voucher_list
    voucher_1.discount_value_type = DiscountValueType.FIXED
    voucher_1.type = VoucherType.SHIPPING
    voucher_2.discount_value_type = DiscountValueType.FIXED
    voucher_2.type = VoucherType.ENTIRE_ORDER
    Voucher.objects.bulk_update([voucher_1, voucher_2], ["discount_value_type", "type"])

    # apply shipping voucher
    voucher_listing_1 = voucher_1.channel_listings.get(channel=order.channel)
    voucher_1_discount = Money(voucher_listing_1.discount_value, currency)
    shipping_price_after_discount = undiscounted_shipping_price - voucher_1_discount
    order.voucher = voucher_1
    order.voucher_code = voucher_1.codes.first().code
    create_or_update_voucher_discount_objects_for_order(order)
    order, lines = fetch_order_prices_if_expired(order, plugins_manager, None, True)

    assert order.undiscounted_base_shipping_price == undiscounted_shipping_price
    assert order.base_shipping_price == shipping_price_after_discount
    assert order.shipping_price_net == shipping_price_after_discount
    assert order.shipping_price_gross == quantize_price(
        shipping_price_after_discount * tax_rate, currency
    )
    discount = order.discounts.get()
    assert discount.amount == voucher_1_discount

    # apply entire order voucher
    voucher_listing_2 = voucher_2.channel_listings.get(channel=order.channel)
    voucher_2_discount_value = Decimal("20")
    voucher_listing_2.discount_value = voucher_2_discount_value
    voucher_listing_2.save(update_fields=["discount_value"])
    order.voucher = voucher_2
    order.voucher_code = voucher_2.codes.first().code

    # when
    create_or_update_voucher_discount_objects_for_order(order)
    order, lines = fetch_order_prices_if_expired(order, plugins_manager, None, True)

    # then
    line_1, line_2 = lines
    assert line_1.base_unit_price_amount == line_1.undiscounted_base_unit_price_amount
    assert line_2.base_unit_price_amount == line_2.undiscounted_base_unit_price_amount

    line_1_total_base_price = line_1.base_unit_price_amount * line_1.quantity
    line_2_total_base_price = line_2.base_unit_price_amount * line_2.quantity
    base_subtotal = line_1_total_base_price + line_2_total_base_price
    line_1_discount_portion = (
        line_1_total_base_price / base_subtotal * voucher_2_discount_value
    )
    line_2_discount_portion = voucher_2_discount_value - line_1_discount_portion

    assert line_1.total_price_net_amount == quantize_price(
        line_1_total_base_price - line_1_discount_portion, currency
    )
    assert line_1.total_price_gross_amount == quantize_price(
        line_1.total_price_net_amount * tax_rate, currency
    )
    assert (
        line_1.undiscounted_total_price_net_amount
        == line_1.undiscounted_base_unit_price_amount * line_1.quantity
    )
    assert (
        line_1.undiscounted_total_price_gross_amount
        == line_1.undiscounted_total_price_net_amount * tax_rate
    )

    assert line_1.unit_discount_amount == 0
    assert line_1.unit_discount_value == 0
    assert line_1.unit_discount_type is None
    assert line_1.unit_discount_reason is None
    assert not line_1.discounts.exists()

    assert line_2.total_price_net_amount == quantize_price(
        line_2_total_base_price - line_2_discount_portion, currency
    )
    assert line_2.total_price_gross_amount == quantize_price(
        line_2.total_price_net_amount * tax_rate, currency
    )
    assert (
        line_2.undiscounted_total_price_net_amount
        == line_2.undiscounted_base_unit_price_amount * line_2.quantity
    )
    assert (
        line_2.undiscounted_total_price_gross_amount
        == line_2.undiscounted_total_price_net_amount * tax_rate
    )

    assert line_2.unit_discount_amount == 0
    assert line_2.unit_discount_value == 0
    assert line_2.unit_discount_type is None
    assert line_2.unit_discount_reason is None
    assert not line_2.discounts.exists()

    discount.refresh_from_db()
    assert discount.amount_value == voucher_2_discount_value
    assert discount.value_type == voucher_2.discount_value_type
    assert discount.type == DiscountType.VOUCHER
    assert discount.reason == f"Voucher code: {order.voucher_code}"
    assert discount.value == voucher_2_discount_value

    assert order.base_shipping_price == undiscounted_shipping_price
    assert order.shipping_price_net == undiscounted_shipping_price
    assert order.shipping_price_gross == undiscounted_shipping_price * tax_rate

    assert (
        order.subtotal_net_amount
        == undiscounted_subtotal.amount - voucher_2_discount_value
    )
    assert (
        order.subtotal_gross_amount
        == (undiscounted_subtotal.amount - voucher_2_discount_value) * tax_rate
    )
    assert (
        order.total_net_amount
        == order.subtotal_net_amount + order.base_shipping_price_amount
    )
    assert (
        order.total_gross_amount
        == (order.subtotal_net_amount + order.base_shipping_price_amount) * tax_rate
    )
    assert (
        order.undiscounted_total_net
        == undiscounted_subtotal + undiscounted_shipping_price
    )
    assert (
        order.undiscounted_total_gross
        == (undiscounted_subtotal + undiscounted_shipping_price) * tax_rate
    )


def test_update_voucher_discount_entire_order_with_shipping(
    order_with_lines,
    plugins_manager,
    tax_configuration_flat_rates,
    voucher_list,
):
    # given
    order = order_with_lines
    order.status = OrderStatus.UNCONFIRMED
    tax_rate = Decimal("1.23")

    lines = order.lines.all()
    undiscounted_shipping_price = order.undiscounted_base_shipping_price
    currency = order.currency
    undiscounted_subtotal = zero_money(currency)
    for line in lines:
        undiscounted_subtotal += line.undiscounted_base_unit_price * line.quantity

    # prepare vouchers
    voucher_1, voucher_2, _ = voucher_list
    voucher_1.discount_value_type = DiscountValueType.FIXED
    voucher_1.type = VoucherType.ENTIRE_ORDER
    voucher_2.discount_value_type = DiscountValueType.FIXED
    voucher_2.type = VoucherType.SHIPPING
    Voucher.objects.bulk_update([voucher_1, voucher_2], ["discount_value_type", "type"])

    # apply entire order voucher
    voucher_listing_1 = voucher_1.channel_listings.get(channel=order.channel)
    voucher_1_discount = Money(voucher_listing_1.discount_value, currency)
    order.voucher = voucher_1
    order.voucher_code = voucher_1.codes.first().code
    create_or_update_voucher_discount_objects_for_order(order)
    order, lines = fetch_order_prices_if_expired(order, plugins_manager, None, True)

    assert order.subtotal_net_amount == quantize_price(
        undiscounted_subtotal.amount - voucher_1_discount.amount, currency
    )
    assert order.total_net_amount == quantize_price(
        order.subtotal_net_amount + undiscounted_shipping_price.amount, currency
    )
    discount = order.discounts.get()
    assert discount.amount == voucher_1_discount

    # apply shipping voucher
    voucher_listing_2 = voucher_2.channel_listings.get(channel=order.channel)
    voucher_2_discount = Money(voucher_listing_2.discount_value, currency)
    shipping_price_after_discount = undiscounted_shipping_price - voucher_2_discount
    order.voucher = voucher_2
    order.voucher_code = voucher_2.codes.first().code

    # when
    create_or_update_voucher_discount_objects_for_order(order)
    order, lines = fetch_order_prices_if_expired(order, plugins_manager, None, True)

    # then
    line_1, line_2 = lines
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
    assert line_1.unit_discount_value == 0

    assert line_2.base_unit_price_amount == line_2.undiscounted_base_unit_price_amount
    assert (
        line_2.total_price_gross_amount
        == line_2.undiscounted_base_unit_price_amount * line_2.quantity * tax_rate
    )
    assert (
        line_2.undiscounted_total_price_gross_amount
        == line_2.undiscounted_base_unit_price_amount * line_2.quantity * tax_rate
    )
    assert line_2.unit_discount_amount == 0
    assert line_2.unit_discount_type is None
    assert line_2.unit_discount_reason is None
    assert line_2.unit_discount_value == 0

    discount.refresh_from_db()
    assert discount.amount == voucher_2_discount
    assert discount.value_type == voucher_2.discount_value_type
    assert discount.type == DiscountType.VOUCHER
    assert discount.reason == f"Voucher code: {order.voucher_code}"
    assert discount.value == voucher_2_discount.amount

    assert order.undiscounted_base_shipping_price == undiscounted_shipping_price
    assert order.base_shipping_price == shipping_price_after_discount
    assert order.shipping_price_net == shipping_price_after_discount
    assert order.shipping_price_gross == quantize_price(
        shipping_price_after_discount * tax_rate, currency
    )

    assert (
        order.undiscounted_total_net
        == undiscounted_subtotal + undiscounted_shipping_price
    )
    assert (
        order.undiscounted_total_gross
        == (undiscounted_subtotal + undiscounted_shipping_price) * tax_rate
    )
    assert order.subtotal_net_amount == undiscounted_subtotal.amount
    assert order.subtotal_gross_amount == undiscounted_subtotal.amount * tax_rate
    assert (
        order.total_net_amount
        == order.subtotal_net_amount + order.base_shipping_price_amount
    )
    assert order.total_gross == quantize_price(
        (order.undiscounted_total_net - voucher_2_discount) * tax_rate, currency
    )


def test_update_voucher_discount_entire_order_with_specific_product(
    order_with_lines,
    plugins_manager,
    tax_configuration_flat_rates,
    voucher_list,
):
    # given
    order = order_with_lines
    order.status = OrderStatus.UNCONFIRMED
    tax_rate = Decimal("1.23")

    lines = order.lines.all()
    line_1, line_2 = lines
    undiscounted_shipping_price = order.undiscounted_base_shipping_price
    currency = order.currency
    undiscounted_subtotal = zero_money(currency)
    for line in lines:
        undiscounted_subtotal += line.undiscounted_base_unit_price * line.quantity

    # prepare vouchers
    voucher_1, voucher_2, _ = voucher_list
    voucher_1.discount_value_type = DiscountValueType.FIXED
    voucher_1.type = VoucherType.ENTIRE_ORDER
    voucher_2.discount_value_type = DiscountValueType.FIXED
    voucher_2.type = VoucherType.SPECIFIC_PRODUCT
    voucher_2.variants.add(line_1.variant)
    Voucher.objects.bulk_update([voucher_1, voucher_2], ["discount_value_type", "type"])

    # apply entire order voucher
    voucher_listing_1 = voucher_1.channel_listings.get(channel=order.channel)
    voucher_1_discount = Money(voucher_listing_1.discount_value, currency)
    order.voucher = voucher_1
    order.voucher_code = voucher_1.codes.first().code
    create_or_update_voucher_discount_objects_for_order(order)
    order, lines = fetch_order_prices_if_expired(order, plugins_manager, None, True)

    assert order.subtotal_net_amount == quantize_price(
        undiscounted_subtotal.amount - voucher_1_discount.amount, currency
    )
    assert order.total_net_amount == quantize_price(
        order.subtotal_net_amount + undiscounted_shipping_price.amount, currency
    )
    discount_1 = order.discounts.get()
    assert discount_1.amount == voucher_1_discount

    # apply specific product voucher for line 1 variant
    voucher_listing_2 = voucher_2.channel_listings.get(channel=order.channel)
    voucher_2_unit_discount = voucher_listing_2.discount_value
    order.voucher = voucher_2
    order.voucher_code = voucher_2.codes.first().code

    # when
    create_or_update_voucher_discount_objects_for_order(order)
    order, lines = fetch_order_prices_if_expired(order, plugins_manager, None, True)

    # then
    line_1, line_2 = lines

    assert quantize_price(line_1.base_unit_price_amount, currency) == quantize_price(
        line_1.undiscounted_base_unit_price_amount - voucher_2_unit_discount,
        currency,
    )
    assert line_1.total_price_gross_amount == quantize_price(
        line_1.base_unit_price_amount * line_1.quantity * tax_rate,
        currency,
    )
    assert (
        line_1.undiscounted_total_price_gross_amount
        == line_1.undiscounted_base_unit_price_amount * line_1.quantity * tax_rate
    )
    assert line_1.unit_discount_amount == voucher_2_unit_discount
    assert line_1.unit_discount_type == voucher_2.discount_value_type
    assert line_1.unit_discount_reason == f"Voucher code: {order.voucher_code}"
    assert line_1.unit_discount_value == voucher_2_unit_discount

    assert line_2.base_unit_price_amount == line_2.undiscounted_base_unit_price_amount
    assert (
        line_2.total_price_gross_amount
        == line_2.undiscounted_base_unit_price_amount * line_2.quantity * tax_rate
    )
    assert (
        line_2.undiscounted_total_price_gross_amount
        == line_2.undiscounted_base_unit_price_amount * line_2.quantity * tax_rate
    )
    assert line_2.unit_discount_amount == 0
    assert line_2.unit_discount_type is None
    assert line_2.unit_discount_reason is None
    assert line_2.unit_discount_value == 0

    with pytest.raises(OrderDiscount.DoesNotExist):
        discount_1.refresh_from_db()

    discount_2 = line_1.discounts.get()
    discount_amount_2 = voucher_2_unit_discount * line_1.quantity
    assert discount_2.amount_value == discount_amount_2
    assert discount_2.value_type == voucher_2.discount_value_type
    assert discount_2.type == DiscountType.VOUCHER
    assert discount_2.reason == f"Voucher code: {order.voucher_code}"
    assert discount_2.value == voucher_2_unit_discount

    assert order.base_shipping_price == undiscounted_shipping_price
    assert order.shipping_price_net == undiscounted_shipping_price
    assert order.shipping_price_gross == undiscounted_shipping_price * tax_rate
    assert order.subtotal_net_amount == undiscounted_subtotal.amount - discount_amount_2
    assert (
        order.subtotal_gross_amount
        == (undiscounted_subtotal.amount - discount_amount_2) * tax_rate
    )
    assert (
        order.total_net_amount
        == order.subtotal_net_amount + order.base_shipping_price_amount
    )
    assert (
        order.total_gross_amount
        == (order.subtotal_net_amount + order.base_shipping_price_amount) * tax_rate
    )
    assert (
        order.undiscounted_total_net
        == undiscounted_subtotal + undiscounted_shipping_price
    )
    assert (
        order.undiscounted_total_gross
        == (undiscounted_subtotal + undiscounted_shipping_price) * tax_rate
    )
