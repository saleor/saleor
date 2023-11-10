from collections.abc import Iterable
from decimal import Decimal
from typing import TYPE_CHECKING

from prices import Money, TaxedMoney

from ..core.taxes import zero_money
from ..discount import DiscountType, DiscountValueType, VoucherType
from ..discount.models import OrderDiscount
from ..discount.utils import apply_discount_to_value
from .interface import OrderTaxedPricesData

if TYPE_CHECKING:
    from .models import Order, OrderLine


# We need this function to don't break Avalara Excise.
def base_order_shipping(order: "Order") -> Money:
    return order.base_shipping_price


def base_order_subtotal(order: "Order", lines: Iterable["OrderLine"]) -> Money:
    """Return base order subtotal.

    The subtotal already includes line discounts.
    """
    currency = order.currency
    subtotal = zero_money(currency)
    for line in lines:
        quantity = line.quantity
        base_line_total = line.base_unit_price * quantity
        subtotal += base_line_total
    return subtotal


def base_order_total(order: "Order", lines: Iterable["OrderLine"]) -> Money:
    """Return order total, recalculate, and update order discounts.

    This function returns the order total. All discounts are included in this price.
    Shipping vouchers are included in the shipping price.
    Specific product vouchers are included in line base prices.
    Entire order vouchers are recalculated and updated in this function
    (OrderDiscounts with type `order_discount.type == DiscountType.VOUCHER`).
    Staff order discounts are recalculated and updated in this function
    (OrderDiscounts with type `order_discount.type == DiscountType.MANUAL`).
    """
    currency = order.currency
    undiscounted_subtotal = base_order_subtotal(order, lines)
    shipping_price = order.base_shipping_price

    discounted_subtotal, discounted_shipping_price = apply_order_discounts(
        undiscounted_subtotal, shipping_price, order
    )
    subtotal_discount = undiscounted_subtotal - discounted_subtotal
    if subtotal_discount >= zero_money(currency):
        apply_subtotal_discount_to_order_lines(
            lines, undiscounted_subtotal, subtotal_discount
        )

    return max(undiscounted_subtotal + shipping_price, zero_money(currency))


def base_order_line_total(order_line: "OrderLine") -> OrderTaxedPricesData:
    quantity = order_line.quantity
    price_with_discounts = (
        TaxedMoney(order_line.base_unit_price, order_line.base_unit_price) * quantity
    )
    undiscounted_price = (
        TaxedMoney(
            order_line.undiscounted_base_unit_price,
            order_line.undiscounted_base_unit_price,
        )
        * quantity
    )
    return OrderTaxedPricesData(
        undiscounted_price=undiscounted_price,
        price_with_discounts=price_with_discounts,
    )


def apply_order_discounts(
    subtotal: Money,
    shipping_price: Money,
    order: "Order",
):
    """Calculate order prices after applying discounts.

    Handles manual discounts and voucher discounts: ENTIRE_ORDER and SHIPPING.
    """
    currency = order.currency
    order_discounts_to_update = []
    order_discounts = order.discounts.all()
    for order_discount in order_discounts:
        subtotal_before_discount = subtotal
        shipping_price_before_discount = shipping_price
        if order_discount.type == DiscountType.VOUCHER:
            voucher = order.voucher
            if voucher and voucher.type == VoucherType.ENTIRE_ORDER:
                subtotal = apply_discount_to_value(
                    value=order_discount.value,
                    value_type=order_discount.value_type,
                    currency=currency,
                    price_to_discount=subtotal,
                )
            if voucher and voucher.type == VoucherType.SHIPPING:
                shipping_price = apply_discount_to_value(
                    value=order_discount.value,
                    value_type=order_discount.value_type,
                    currency=currency,
                    price_to_discount=shipping_price,
                )
        elif order_discount.type == DiscountType.MANUAL:
            if order_discount.value_type == DiscountValueType.PERCENTAGE:
                subtotal = apply_discount_to_value(
                    value=order_discount.value,
                    value_type=order_discount.value_type,
                    currency=currency,
                    price_to_discount=subtotal,
                )
                shipping_price = apply_discount_to_value(
                    value=order_discount.value,
                    value_type=order_discount.value_type,
                    currency=currency,
                    price_to_discount=shipping_price,
                )
            else:
                temporary_undiscounted_total = subtotal + shipping_price
                if temporary_undiscounted_total.amount > 0:
                    temporary_total = apply_discount_to_value(
                        value=order_discount.value,
                        value_type=order_discount.value_type,
                        currency=currency,
                        price_to_discount=temporary_undiscounted_total,
                    )
                    total_discount = temporary_undiscounted_total - temporary_total
                    subtotal_discount = (
                        subtotal / temporary_undiscounted_total
                    ) * total_discount
                    shipping_discount = total_discount - subtotal_discount

                    subtotal -= subtotal_discount
                    shipping_price -= shipping_discount
        shipping_discount_amount = shipping_price_before_discount - shipping_price
        subtotal_discount_amount = subtotal_before_discount - subtotal
        total_discount_amount = shipping_discount_amount + subtotal_discount_amount
        if order_discount.amount != total_discount_amount:
            order_discount.amount = total_discount_amount
            order_discounts_to_update.append(order_discount)

    if order_discounts_to_update:
        OrderDiscount.objects.bulk_update(order_discounts_to_update, ["amount_value"])

    return subtotal, shipping_price


def apply_subtotal_discount_to_order_lines(
    lines: Iterable["OrderLine"],
    undiscounted_subtotal: Money,
    subtotal_discount: Money,
):
    """Calculate order line prices after applying discounts to entire order."""
    # Handle order with single line - propagate the whole discount to the single line.
    lines = list(lines)
    lines_count = len(lines)
    if lines_count == 1:
        line = lines[0]
        apply_discount_to_order_line(line, subtotal_discount.amount)

    # Handle order with multiple lines - propagate the order discount proportionally
    # to the lines.
    elif lines_count > 1:
        for idx, line in enumerate(lines):
            if idx < lines_count - 1:
                share = line.total_price_net_amount / undiscounted_subtotal.amount
                line_discount = share * subtotal_discount.amount
                apply_discount_to_order_line(line, line_discount)

        _ensure_order_lines_prices_sum_up_to_order_prices(
            lines, subtotal_discount.amount
        )


def apply_discount_to_order_line(line: "OrderLine", line_discount: Decimal):
    """Calculate order line prices after applying order line disccount.

    Takes an order line and order line discount as an argument and updates
    line total_price, unit_price, base_unit_price and unit_discount fields.
    """
    quantity = line.quantity
    total_price = max(line.total_price_net_amount - line_discount, Decimal("0"))
    line.total_price_net_amount = total_price
    line.total_price_gross_amount = total_price

    unit_price = total_price / quantity
    line.base_unit_price_amount = unit_price
    line.unit_price_net_amount = unit_price
    line.unit_price_gross_amount = unit_price

    unit_discount = line_discount / quantity
    line.unit_discount_amount = unit_discount


def _ensure_order_lines_prices_sum_up_to_order_prices(
    lines: list["OrderLine"],
    subtotal_discount: Decimal,
):
    other_lines_discount = sum(
        [
            line.undiscounted_total_price_net_amount - line.total_price_net_amount
            for line in lines[:-1]
        ]
    )
    last_line_discount = subtotal_discount - other_lines_discount
    apply_discount_to_order_line(lines[-1], last_line_discount)


# def _ensure_order_lines_prices_sum_up_to_order_prices(
#     lines: list["OrderLine"],
#     undiscounted_subtotal: Decimal,
#     subtotal_discount: Decimal,
# ):
#     other_lines_total = sum([line.total_price_net_amount for line in lines[:-1]])
#     discounted_subtotal = undiscounted_subtotal - subtotal_discount
#     last_line_total = discounted_subtotal - other_lines_total
#
#     last_line = lines[-1]
#     last_line.total_price_net_amount = last_line_total
#
#     quantity = last_line.quantity
#     unit_price = last_line_total / quantity
#     last_line.base_unit_price_amount = unit_price
#     last_line.unit_price_net_amount = unit_price
#     last_line.unit_price_gross_amount = unit_price
#
#     other_lines_discount = sum([line.unit_discount_amount * line.quantity for line in lines[:-1]])
#     last_line_discount = subtotal_discount - other_lines_discount
#     unit_discount = last_line_discount / quantity
#     last_line.unit_discount = unit_discount
