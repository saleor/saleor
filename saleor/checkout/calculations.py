from typing import TYPE_CHECKING

from ..extensions.manager import get_extensions_manager

if TYPE_CHECKING:
    from prices import TaxedMoney
    from .models import Checkout, CheckoutLine
    from ..discount.types import DiscountsListType


def get_checkout_shipping_price(
    checkout: "Checkout", discounts: "DiscountsListType" = None
) -> "TaxedMoney":
    """Return checkout price without taking in account aby plugins and extensions.

    It takes in account all extensions.
    """
    return get_extensions_manager().calculate_checkout_shipping(checkout, discounts)


def get_checkout_subtotal(
    checkout: "Checkout", discounts: "DiscountsListType" = None
) -> "TaxedMoney":
    """Return the total cost of the checkout prior to shipping.

    It takes in account all extensions.
    """
    return get_extensions_manager().calculate_checkout_subtotal(checkout, discounts)


def get_checkout_total(
    checkout: "Checkout", discounts: "DiscountsListType" = None
) -> "TaxedMoney":
    """Return the total cost of the checkout.

    It takes in account all extensions.
    """
    return get_extensions_manager().calculate_checkout_total(checkout, discounts)


def get_checkout_line_total(
    line: "CheckoutLine", discounts: "DiscountsListType" = None
) -> "TaxedMoney":
    """Return the total price of this line.

    It takes in account all extensions.
    """
    return get_extensions_manager().calculate_checkout_line_total(line, discounts)
