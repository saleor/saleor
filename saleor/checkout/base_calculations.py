"""Contain functions which are base for calculating checkout properties.

It's recommended to use functions from calculations.py module to take in account plugin
manager.
"""

from decimal import Decimal
from typing import TYPE_CHECKING, Iterable, List, Optional

from prices import TaxedMoney

from ..core.prices import quantize_price
from ..core.taxes import zero_taxed_money
from ..discount import DiscountInfo
from .fetch import CheckoutLineInfo

if TYPE_CHECKING:
    # flake8: noqa
    from ..channel.models import Channel
    from ..checkout.fetch import CheckoutInfo
    from ..product.models import (
        Collection,
        Product,
        ProductVariant,
        ProductVariantChannelListing,
    )
    from .models import Checkout, CheckoutLine


def base_checkout_shipping_price(
    checkout_info: "CheckoutInfo", lines=None
) -> TaxedMoney:
    """Return checkout shipping price."""
    # FIXME: Optimize checkout.is_shipping_required
    shipping_method = checkout_info.shipping_method

    if lines is not None and all(isinstance(line, CheckoutLineInfo) for line in lines):
        from .utils import is_shipping_required

        shipping_required = is_shipping_required(lines)
    else:
        shipping_required = checkout_info.checkout.is_shipping_required()

    if not shipping_method or not shipping_required:
        return zero_taxed_money(checkout_info.checkout.currency)
    shipping_price = shipping_method.channel_listings.get(
        channel_id=checkout_info.checkout.channel_id,
    ).get_total()

    return quantize_price(
        TaxedMoney(net=shipping_price, gross=shipping_price), shipping_price.currency
    )


def base_checkout_subtotal(line_totals: List[TaxedMoney], currency: str) -> TaxedMoney:
    """Return the total cost of all checkout lines."""
    return sum(line_totals, zero_taxed_money(currency))


def base_checkout_total(
    subtotal: TaxedMoney,
    shipping_price: TaxedMoney,
    discount: TaxedMoney,
    currency: str,
) -> TaxedMoney:
    """Return the total cost of the checkout."""
    total = subtotal + shipping_price - discount
    return max(total, zero_taxed_money(currency))


def base_checkout_line_total(
    checkout_line_info: "CheckoutLineInfo",
    channel: "Channel",
    discounts: Optional[Iterable[DiscountInfo]] = None,
) -> TaxedMoney:
    """Return the total price of this line."""
    variant = checkout_line_info.variant
    variant_price = variant.get_price(
        checkout_line_info.product,
        checkout_line_info.collections,
        channel,
        checkout_line_info.channel_listing,
        discounts or [],
    )
    amount = checkout_line_info.line.quantity * variant_price
    price = quantize_price(amount, amount.currency)
    return TaxedMoney(net=price, gross=price)


def base_tax_rate(price: TaxedMoney):
    tax_rate = Decimal("0.0")
    # The condition will return False when unit_price.gross is 0.0
    if not isinstance(price, Decimal) and price.gross:
        tax_rate = price.tax / price.net
    return tax_rate


def base_checkout_line_unit_price(total_line_price: TaxedMoney, quantity: int):
    return total_line_price / quantity
