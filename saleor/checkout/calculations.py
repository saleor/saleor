from typing import TYPE_CHECKING, Iterable, Optional

from ..core.prices import quantize_price
from ..core.taxes import zero_taxed_money
from ..discount import DiscountInfo
from ..plugins.manager import get_plugins_manager

if TYPE_CHECKING:
    from prices import TaxedMoney
    from .models import Checkout, CheckoutLine


def checkout_shipping_price(
    *,
    checkout: "Checkout",
    lines: Iterable["CheckoutLine"],
    discounts: Optional[Iterable[DiscountInfo]] = None,
) -> "TaxedMoney":
    """Return checkout shipping price.

    It takes in account all plugins.
    """
    calculated_checkout_shipping = get_plugins_manager().calculate_checkout_shipping(
        checkout, lines, discounts or []
    )
    return quantize_price(calculated_checkout_shipping, checkout.currency)


def checkout_subtotal(
    *,
    checkout: "Checkout",
    lines: Iterable["CheckoutLine"],
    discounts: Optional[Iterable[DiscountInfo]] = None,
) -> "TaxedMoney":
    """Return the total cost of all the checkout lines, taxes included.

    It takes in account all plugins.
    """
    calculated_checkout_subtotal = get_plugins_manager().calculate_checkout_subtotal(
        checkout, lines, discounts or []
    )
    return quantize_price(calculated_checkout_subtotal, checkout.currency)


def calculate_checkout_total_with_gift_cards(
    checkout: "Checkout", discounts: Optional[Iterable[DiscountInfo]] = None
) -> "TaxedMoney":
    total = (
        checkout_total(checkout=checkout, lines=list(checkout), discounts=discounts,)
        - checkout.get_total_gift_cards_balance()
    )

    return max(total, zero_taxed_money(total.currency))


def checkout_total(
    *,
    checkout: "Checkout",
    lines: Iterable["CheckoutLine"],
    discounts: Optional[Iterable[DiscountInfo]] = None,
) -> "TaxedMoney":
    """Return the total cost of the checkout.

    Total is a cost of all lines and shipping fees, minus checkout discounts,
    taxes included.

    It takes in account all plugins.
    """
    calculated_checkout_total = get_plugins_manager().calculate_checkout_total(
        checkout, lines, discounts or []
    )
    return quantize_price(calculated_checkout_total, checkout.currency)


def checkout_line_total(
    *, line: "CheckoutLine", discounts: Optional[Iterable[DiscountInfo]] = None
) -> "TaxedMoney":
    """Return the total price of provided line, taxes included.

    It takes in account all plugins.
    """
    calculated_line_total = get_plugins_manager().calculate_checkout_line_total(
        line, discounts or []
    )
    return quantize_price(calculated_line_total, line.checkout.currency)
