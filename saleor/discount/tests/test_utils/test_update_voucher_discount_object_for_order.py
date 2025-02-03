from copy import deepcopy
from decimal import Decimal

import graphene
import pytest

from ....core.prices import Money, quantize_price
from ....core.taxes import zero_money
from ....graphql.order.types import OrderLine
from ....order import OrderStatus
from ....order.calculations import fetch_order_prices_if_expired
from ... import DiscountType, DiscountValueType, VoucherType
from ...models import (
    OrderDiscount,
    OrderLineDiscount,
    PromotionRule,
    Voucher,
)
from ...utils.voucher import (
    create_or_update_voucher_discount_objects_for_order,
)


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
        undiscounted_subtotal += line.base_unit_price * line.quantity

    # prepare vouchers
    voucher_1, voucher_2, _ = voucher_list
    for voucher in voucher_list:
        voucher.discount_value_type = DiscountValueType.FIXED
        voucher.type = VoucherType.SPECIFIC_PRODUCT
    Voucher.objects.bulk_update(voucher_list, ["discount_value_type", "type"])
    voucher_1.variants.add(line_1.variant)
    voucher_2.variants.add(line_2.variant)

    # apply voucher 1
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

    # apply voucher 2
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
