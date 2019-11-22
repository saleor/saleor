from typing import TYPE_CHECKING

from ..extensions.manager import get_extensions_manager

if TYPE_CHECKING:
    from prices import TaxedMoney
    from .models import Checkout, CheckoutLine
    from ..discount.types import DiscountsListType


def checkout_shipping_price(
    checkout: "Checkout", discounts: "DiscountsListType" = None
) -> "TaxedMoney":
    """Return checkout shipping price.

    It takes in account all extensions.
    """
    return get_extensions_manager().calculate_checkout_shipping(checkout, discounts)


def checkout_subtotal(
    checkout: "Checkout", discounts: "DiscountsListType" = None
) -> "TaxedMoney":
    """Return the total cost of all the checkout lines, taxes included.

    It takes in account all extensions.
    """
    return get_extensions_manager().calculate_checkout_subtotal(checkout, discounts)


def checkout_total(
    checkout: "Checkout", discounts: "DiscountsListType" = None
) -> "TaxedMoney":
    """Return the total cost of the checkout.

    Total is a cost of all lines and shipping fees, minus checkout discounts,
    taxes included.

    It takes in account all extensions.
    """
    return get_extensions_manager().calculate_checkout_total(checkout, discounts)


def checkout_line_total(
    line: "CheckoutLine", discounts: "DiscountsListType" = None
) -> "TaxedMoney":
    """Return the total price of provided line, taxes included.

    It takes in account all extensions.
    """
    return get_extensions_manager().calculate_checkout_line_total(line, discounts)
