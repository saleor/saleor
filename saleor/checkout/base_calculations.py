"""Contain functions which are base for calculating checkout properties.

It's recommended to use functions from calculations.py module to take in account plugin
manager.
"""

from decimal import Decimal
from typing import TYPE_CHECKING, Iterable, Optional

from prices import Money, TaxedMoney

from ..core.prices import quantize_price
from ..core.taxes import zero_money, zero_taxed_money
from ..discount import DiscountInfo
from ..order.interface import OrderTaxedPricesData

if TYPE_CHECKING:
    from ..channel.models import Channel
    from ..checkout.fetch import CheckoutInfo
    from ..order.models import OrderLine
    from .fetch import CheckoutLineInfo, ShippingMethodInfo


def calculate_base_line_unit_price(
    line_info: "CheckoutLineInfo",
    channel: "Channel",
    discounts: Optional[Iterable[DiscountInfo]] = None,
) -> Money:
    """Calculate line unit price.

    Unit price includes discount from sale and voucher A voucher is added to the unit
    price when line's product matches to products applicable for the voucher.
    """
    variant = line_info.variant
    variant_price = variant.get_price(
        line_info.product,
        line_info.collections,
        channel,
        line_info.channel_listing,
        discounts or [],
        line_info.line.price_override,
    )

    # TODO IN separate PR:
    # We should include apply_once_per_order into unit price.
    if line_info.voucher and not line_info.voucher.apply_once_per_order:
        unit_price = max(
            variant_price
            - line_info.voucher.get_discount_amount_for(variant_price, channel=channel),
            zero_money(variant_price.currency),
        )
    else:
        unit_price = variant_price

    return quantize_price(unit_price, unit_price.currency)


def calculate_base_line_total_price(
    line_info: "CheckoutLineInfo",
    channel: "Channel",
    discounts: Optional[Iterable[DiscountInfo]] = None,
) -> Money:
    """Calculate line total prices including sales and specific products vouchers."""
    unit_price = calculate_base_line_unit_price(
        line_info=line_info, channel=channel, discounts=discounts
    )
    if line_info.voucher and line_info.voucher.apply_once_per_order:
        variant_price_with_discounts = max(
            unit_price
            - line_info.voucher.get_discount_amount_for(unit_price, channel=channel),
            zero_money(unit_price.currency),
        )
        # we add -1 as we handle a case when voucher is applied only to single line
        # of the cheapest line
        quantity_without_voucher = line_info.line.quantity - 1
        total_price = (
            unit_price * quantity_without_voucher + variant_price_with_discounts
        )
    else:
        total_price = unit_price * line_info.line.quantity

    return quantize_price(total_price, total_price.currency)


def base_checkout_delivery_price(checkout_info: "CheckoutInfo", lines=None) -> Money:
    """Calculate base (untaxed) price for any kind of delivery method."""
    from .fetch import ShippingMethodInfo

    delivery_method_info = checkout_info.delivery_method_info

    if isinstance(delivery_method_info, ShippingMethodInfo):
        return calculate_base_price_for_shipping_method(
            checkout_info, delivery_method_info, lines
        )

    return zero_money(checkout_info.checkout.currency)


def calculate_base_price_for_shipping_method(
    checkout_info: "CheckoutInfo",
    shipping_method_info: "ShippingMethodInfo",
    lines=None,
) -> Money:
    """Return checkout shipping price."""
    from .fetch import CheckoutLineInfo

    # FIXME: Optimize checkout.is_shipping_required
    shipping_method = shipping_method_info.delivery_method

    if lines is not None and all(isinstance(line, CheckoutLineInfo) for line in lines):
        from .utils import is_shipping_required

        shipping_required = is_shipping_required(lines)
    else:
        shipping_required = checkout_info.checkout.is_shipping_required()

    if not shipping_method or not shipping_required:
        return zero_money(checkout_info.checkout.currency)

    return quantize_price(
        shipping_method.price,
        checkout_info.checkout.currency,
    )


def base_checkout_total(
    subtotal: TaxedMoney,
    shipping_price: TaxedMoney,
    discount: Money,
    currency: str,
) -> TaxedMoney:
    """Return the total cost of the checkout."""
    zero = zero_taxed_money(currency)
    # TODO In separate PR:
    # FIX, Voucher should be included in ShippingPrice or Subtotal, depends on voucher
    # type
    total = subtotal + shipping_price - discount
    # Discount is subtracted from both gross and net values, which may cause negative
    # net value if we are having a discount that covers whole price.
    # Comparing TaxedMoney objects works only on gross values. That is why we are
    # explicitly returning zero_taxed_money if total.gross is less or equal zero.
    if total.gross <= zero.gross:
        return zero
    return total


def base_checkout_subtotal(
    checkout_lines: Iterable["CheckoutLineInfo"],
    channel: "Channel",
    currency: str,
    discounts: Optional[Iterable[DiscountInfo]] = None,
) -> Money:
    line_totals = [
        calculate_base_line_total_price(
            line,
            channel,
            discounts,
        )
        for line in checkout_lines
    ]

    return sum(line_totals, zero_money(currency))


def base_checkout_line_total(
    checkout_line_info: "CheckoutLineInfo",
    channel: "Channel",
    discounts: Optional[Iterable[DiscountInfo]] = None,
) -> Money:
    """Return the total price of this line."""
    return calculate_base_line_total_price(
        line_info=checkout_line_info, channel=channel, discounts=discounts
    )


def base_order_line_total(order_line: "OrderLine") -> OrderTaxedPricesData:
    quantity = order_line.quantity
    return OrderTaxedPricesData(
        undiscounted_price=order_line.undiscounted_unit_price * quantity,
        price_with_discounts=order_line.unit_price * quantity,
    )


def base_tax_rate(price: TaxedMoney):
    tax_rate = Decimal("0.0")
    # The condition will return False when unit_price.gross or unit_price.net is 0.0
    if not isinstance(price, Decimal) and all((price.gross, price.net)):
        tax_rate = price.tax / price.net
    return tax_rate


def base_checkout_line_unit_price(
    checkout_line_info: "CheckoutLineInfo",
    channel: "Channel",
    discounts: Optional[Iterable[DiscountInfo]] = None,
) -> Money:
    return calculate_base_line_unit_price(
        line_info=checkout_line_info, channel=channel, discounts=discounts
    )
