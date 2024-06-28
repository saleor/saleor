from collections.abc import Iterable
from typing import TYPE_CHECKING, Optional

from django.conf import settings
from prices import Money, TaxedMoney

from ..core.db.connection import allow_writer
from ..core.prices import quantize_price
from ..core.taxes import zero_money
from ..discount import DiscountType, DiscountValueType, VoucherType
from ..discount.models import OrderDiscount
from ..discount.utils.manual_discount import apply_discount_to_value
from ..discount.utils.voucher import is_order_level_voucher
from ..shipping.models import ShippingMethodChannelListing
from .interface import OrderTaxedPricesData

if TYPE_CHECKING:
    from .models import Order, OrderLine


# We need this function to don't break Avalara Excise.
def base_order_shipping(order: "Order") -> Money:
    return order.base_shipping_price


def base_order_subtotal(order: "Order", lines: Iterable["OrderLine"]) -> Money:
    """Return order subtotal.

    May include order line level discounts, like promotions, specific product vouchers
    and manual line discounts.
    Does not include order level discounts, like entire order vouchers and manual
    order discounts.
    """
    currency = order.currency
    subtotal = zero_money(currency)
    for line in lines:
        quantity = line.quantity
        base_line_total = line.base_unit_price * quantity
        subtotal += base_line_total

    return quantize_price(subtotal, currency)


def base_order_total(
    order: "Order",
    lines: Iterable["OrderLine"],
    database_connection_name: str = settings.DATABASE_CONNECTION_DEFAULT_NAME,
) -> Money:
    """Return order total, recalculate, and update order discounts.

    All discounts are included in this price.
    """
    subtotal, shipping_price = apply_order_discounts(
        order,
        lines,
        assign_prices=False,
        database_connection_name=database_connection_name,
    )
    return subtotal + shipping_price


def base_order_line_total(order_line: "OrderLine") -> OrderTaxedPricesData:
    """Return order line base total.

    May include order line level discounts, like promotions, specific product vouchers
    and manual line discounts.
    Does not include order level discounts, like entire order vouchers and manual
    order discounts.
    """
    quantity = order_line.quantity
    price_with_line_discounts = (
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
        price_with_discounts=price_with_line_discounts,
    )


def propagate_order_discount_on_order_prices(
    order: "Order",
    lines: Iterable["OrderLine"],
) -> tuple[Money, Money]:
    """Propagate the order discount on order.subtotal and order.shipping_price.

    The function returns the subtotal and shipping price after applying the order
    discount.
    """
    base_subtotal = base_order_subtotal(order, lines)
    # TODO (SHOPX-875): add undiscounted_base_shipping_price field to Order model,
    # and use it here
    base_shipping_price = order.base_shipping_price
    subtotal = base_subtotal
    shipping_price = base_shipping_price
    currency = order.currency
    order_discounts_to_update = []

    shipping_voucher_discount = None
    for order_discount in order.discounts.all():
        subtotal_before_discount = subtotal
        shipping_price_before_discount = shipping_price
        if order_discount.type == DiscountType.VOUCHER:
            voucher = order_discount.voucher
            if is_order_level_voucher(voucher):
                subtotal = apply_discount_to_value(
                    value=order_discount.value,
                    value_type=order_discount.value_type,
                    currency=currency,
                    price_to_discount=subtotal,
                )
            elif voucher and voucher.type == VoucherType.SHIPPING:
                shipping_voucher_discount = order_discount
        elif order_discount.type == DiscountType.ORDER_PROMOTION:
            subtotal = apply_discount_to_value(
                value=order_discount.value,
                value_type=order_discount.value_type,
                currency=currency,
                price_to_discount=subtotal,
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
            elif order_discount.value_type == DiscountValueType.FIXED:
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

    # Apply shipping voucher discount
    if shipping_voucher_discount:
        shipping_price = apply_discount_to_value(
            value=shipping_voucher_discount.value,
            value_type=shipping_voucher_discount.value_type,
            currency=currency,
            price_to_discount=shipping_price,
        )
        discount_amount = shipping_price_before_discount - shipping_price
        if shipping_voucher_discount.amount != discount_amount:
            shipping_voucher_discount.amount = discount_amount
            order_discounts_to_update.append(shipping_voucher_discount)

    if order_discounts_to_update:
        OrderDiscount.objects.bulk_update(order_discounts_to_update, ["amount_value"])

    return subtotal, shipping_price


def apply_order_discounts(
    order: "Order",
    lines: Iterable["OrderLine"],
    assign_prices=True,
    database_connection_name: str = settings.DATABASE_CONNECTION_DEFAULT_NAME,
) -> tuple[Money, Money]:
    """Calculate prices after applying order level discounts.

    Handles manual discounts and ENTIRE_ORDER vouchers.
    Shipping vouchers are included in the base shipping price.
    Specific product vouchers are included in line base prices.
    Entire order vouchers are recalculated and updated in this function
    (OrderDiscounts with type `order_discount.type == DiscountType.VOUCHER`).
    Staff order discounts are recalculated and updated in this function
    (OrderDiscounts with type `order_discount.type == DiscountType.MANUAL`).
    """
    base_subtotal = base_order_subtotal(order, lines)

    subtotal, shipping_price = propagate_order_discount_on_order_prices(order, lines)

    if assign_prices:
        assign_order_prices(
            order,
            lines,
            subtotal,
            shipping_price,
            database_connection_name=database_connection_name,
        )
        subtotal_discount = base_subtotal - subtotal
        apply_subtotal_discount_to_order_lines(lines, base_subtotal, subtotal_discount)

    return subtotal, shipping_price


def _get_total_price_with_subtotal_discount_for_order_line(
    line: "OrderLine", discount: Money
) -> Money:
    """Get subtotal discount for a given order line."""

    currency = discount.currency
    # This price includes line level discounts, but not entire order ones.
    base_line_total = base_order_line_total(line).price_with_discounts.net
    total_price = max(base_line_total - discount, zero_money(currency))
    return total_price


def propagate_order_discount_on_order_lines_prices(
    lines: Iterable["OrderLine"],
    base_subtotal: Money,
    subtotal_discount: Money,
) -> Iterable[tuple["OrderLine", Money]]:
    """Return the line with new total price.

    The total price contains propagated order discount.
    """
    lines = list(lines)
    lines_count = len(lines)
    if lines_count == 1:
        line = lines[0]
        yield (
            line,
            _get_total_price_with_subtotal_discount_for_order_line(
                line, subtotal_discount
            ),
        )

    # Handle order with multiple lines - propagate the order discount proportionally
    # to the lines.
    elif lines_count > 1:
        remaining_discount = subtotal_discount
        for idx, line in enumerate(lines):
            if not base_subtotal.amount:
                yield line, zero_money(base_subtotal.currency)
            elif idx < lines_count - 1:
                share = (
                    line.base_unit_price_amount * line.quantity / base_subtotal.amount
                )
                discount = min(share * subtotal_discount, base_subtotal)
                yield (
                    line,
                    _get_total_price_with_subtotal_discount_for_order_line(
                        line, discount
                    ),
                )
                remaining_discount -= discount
            else:
                yield (
                    line,
                    _get_total_price_with_subtotal_discount_for_order_line(
                        line, remaining_discount
                    ),
                )


def get_total_price_with_subtotal_discount_for_order_line(
    line: "OrderLine",
    lines: Iterable["OrderLine"],
    base_subtotal: Money,
    subtotal_discount: Money,
) -> Optional[Money]:
    for order_line, total_price in propagate_order_discount_on_order_lines_prices(
        lines, base_subtotal, subtotal_discount
    ):
        if line.id == order_line.id:
            return total_price
    return None


def apply_subtotal_discount_to_order_lines(
    lines: Iterable["OrderLine"],
    base_subtotal: Money,
    subtotal_discount: Money,
):
    """Calculate order lines prices after applying discounts to entire subtotal."""
    # Handle order with single line - propagate the whole discount to the single line.
    for line, total_price in propagate_order_discount_on_order_lines_prices(
        lines, base_subtotal, subtotal_discount
    ):
        assign_order_line_prices(line, total_price)


def assign_order_line_prices(line: "OrderLine", total_price: Money):
    currency = total_price.currency
    line.total_price_net = quantize_price(total_price, currency)
    line.total_price_gross = line.total_price_net
    line.undiscounted_total_price_gross_amount = (
        line.undiscounted_total_price_net_amount
    )

    quantity = line.quantity
    if quantity > 0:
        unit_price = total_price / quantity
        line.unit_price_net = unit_price
        line.unit_price_gross = unit_price

        undiscounted_unit_price = line.undiscounted_total_price_net_amount / quantity
        line.undiscounted_unit_price_net_amount = undiscounted_unit_price
        line.undiscounted_unit_price_gross_amount = undiscounted_unit_price


def assign_order_prices(
    order: "Order",
    lines: Iterable["OrderLine"],
    subtotal: Money,
    shipping_price: Money,
    database_connection_name: str = settings.DATABASE_CONNECTION_DEFAULT_NAME,
):
    # TODO (SHOPX-875): set order.base_shipping_price as this price should include
    # the shipping discount - must be done together with adding
    # undiscounted_base_shipping_price to Order model
    order.shipping_price_net_amount = shipping_price.amount
    order.shipping_price_gross_amount = shipping_price.amount
    order.total_net_amount = subtotal.amount + shipping_price.amount
    order.total_gross_amount = subtotal.amount + shipping_price.amount

    order.subtotal_net_amount = subtotal.amount
    order.subtotal_gross_amount = subtotal.amount

    undiscounted_total = undiscounted_order_total(
        order, lines, database_connection_name=database_connection_name
    )
    order.undiscounted_total_net_amount = undiscounted_total.amount
    order.undiscounted_total_gross_amount = undiscounted_total.amount


def undiscounted_order_shipping(
    order: "Order",
    database_connection_name: str = settings.DATABASE_CONNECTION_DEFAULT_NAME,
) -> Money:
    """Return shipping price without any discounts."""
    # TODO: add undiscounted_shipping_price field to order model.
    # https://github.com/saleor/saleor/issues/14915

    with allow_writer():
        # TODO: load shipping_method with dataloader and pass as an argument
        shipping_method = order.shipping_method

    if shipping_method:
        if (
            listing := ShippingMethodChannelListing.objects.using(
                database_connection_name
            )
            .filter(channel=order.channel, shipping_method=shipping_method)
            .first()
        ):
            return Money(listing.price_amount, order.currency)
    return zero_money(order.currency)


def undiscounted_order_subtotal(order: "Order", lines: Iterable["OrderLine"]) -> Money:
    """Return order subtotal without any discounts."""
    currency = order.currency
    subtotal = zero_money(currency)
    for line in lines:
        undiscounted_line_total = line.undiscounted_unit_price.net * line.quantity
        subtotal += undiscounted_line_total
    return quantize_price(subtotal, currency)


def undiscounted_order_total(
    order: "Order",
    lines: Iterable["OrderLine"],
    database_connection_name: str = settings.DATABASE_CONNECTION_DEFAULT_NAME,
) -> Money:
    """Return order total without any discounts."""
    subtotal = undiscounted_order_subtotal(order, lines)
    shipping_price = undiscounted_order_shipping(
        order, database_connection_name=database_connection_name
    )
    return quantize_price(subtotal + shipping_price, order.currency)
