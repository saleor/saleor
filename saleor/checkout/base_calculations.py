"""Contain functions which are base for calculating checkout properties.

It's recommended to use functions from calculations.py module to take in account plugin
manager.
"""

from typing import TYPE_CHECKING, Iterable, List, Optional

from prices import TaxedMoney

from ..core.taxes import quantize_price, zero_taxed_money
from ..discount import DiscountInfo

if TYPE_CHECKING:
    # flake8: noqa
    from .models import Checkout, CheckoutLine


def base_checkout_shipping_price(
    checkout: "Checkout", lines: Iterable["CheckoutLine"]
) -> TaxedMoney:
    """Return checkout shipping price."""
    if not checkout.shipping_method or not checkout.is_shipping_required():
        return zero_taxed_money(checkout.currency)

    shipping_price = checkout.shipping_method.get_total()
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
    line: "CheckoutLine", discounts: Optional[Iterable[DiscountInfo]] = None
) -> TaxedMoney:
    """Return the total price of this line."""
    amount = line.quantity * line.variant.get_price(discounts or [])
    price = quantize_price(amount, amount.currency)
    return TaxedMoney(net=price, gross=price)
