"""Contain functions which are base for calculating checkout properties.

It's recommended to use functions from calculations.py module to take in account plugin
manager.
"""

from typing import TYPE_CHECKING

from prices import TaxedMoney

from ..core.taxes import quantize_price, zero_taxed_money
from ..extensions.manager import get_extensions_manager

if TYPE_CHECKING:
    from .models import Checkout, CheckoutLine
    from ..discount.types import DiscountsListType


def get_base_checkout_shipping_price(
    checkout: "Checkout", discounts: "DiscountsListType" = None
) -> TaxedMoney:
    """Return checkout shipping price."""
    # FIXME: should it take discounts in account?
    if not checkout.shipping_method or not checkout.is_shipping_required():
        return zero_taxed_money(checkout.currency)

    shipping_price = checkout.shipping_method.get_total()
    return quantize_price(
        TaxedMoney(net=shipping_price, gross=shipping_price), shipping_price.currency
    )


def get_base_checkout_subtotal(
    checkout: "Checkout", discounts: "DiscountsListType" = None
) -> TaxedMoney:
    """Return the total cost of all checkout lines."""
    extensions = get_extensions_manager()
    subtotals = (
        extensions.calculate_checkout_line_total(line, discounts) for line in checkout
    )
    return sum(subtotals, zero_taxed_money(checkout.currency))


def get_base_checkout_total(
    checkout: "Checkout", discounts: "DiscountsListType" = None
) -> TaxedMoney:
    """Return the total cost of the checkout."""
    extensions = get_extensions_manager()
    total = (
        extensions.calculate_checkout_subtotal(checkout, discounts)
        + extensions.calculate_checkout_shipping(checkout, discounts)
        - checkout.discount
    )
    return max(total, zero_taxed_money(checkout.currency))


def get_base_checkout_line_total(
    line: "CheckoutLine", discounts: "DiscountsListType" = None
) -> TaxedMoney:
    """Return the total price of this line."""
    amount = line.quantity * line.variant.get_price(discounts)
    price = quantize_price(amount, amount.currency)
    return TaxedMoney(net=price, gross=price)
