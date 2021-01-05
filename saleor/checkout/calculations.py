from typing import TYPE_CHECKING, Iterable, Optional

from ..core.prices import quantize_price
from ..core.taxes import zero_taxed_money
from ..discount import DiscountInfo

if TYPE_CHECKING:
    from prices import TaxedMoney

    from ..account.models import Address
    from ..channel.models import Channel
    from ..plugins.manager import PluginsManager
    from ..product.models import (
        Collection,
        Product,
        ProductVariant,
        ProductVariantChannelListing,
    )
    from . import CheckoutLineInfo
    from .models import Checkout, CheckoutLine


def checkout_shipping_price(
    *,
    manager: "PluginsManager",
    checkout: "Checkout",
    lines: Iterable["CheckoutLineInfo"],
    address: Optional["Address"],
    discounts: Optional[Iterable[DiscountInfo]] = None,
) -> "TaxedMoney":
    """Return checkout shipping price.

    It takes in account all plugins.
    """
    calculated_checkout_shipping = manager.calculate_checkout_shipping(
        checkout, lines, address, discounts or []
    )
    return quantize_price(calculated_checkout_shipping, checkout.currency)


def checkout_subtotal(
    *,
    manager: "PluginsManager",
    checkout: "Checkout",
    lines: Iterable["CheckoutLineInfo"],
    address: Optional["Address"],
    discounts: Optional[Iterable[DiscountInfo]] = None,
) -> "TaxedMoney":
    """Return the total cost of all the checkout lines, taxes included.

    It takes in account all plugins.
    """
    calculated_checkout_subtotal = manager.calculate_checkout_subtotal(
        checkout, lines, address, discounts or []
    )
    return quantize_price(calculated_checkout_subtotal, checkout.currency)


def calculate_checkout_total_with_gift_cards(
    manager: "PluginsManager",
    checkout: "Checkout",
    lines: Iterable["CheckoutLineInfo"],
    address: Optional["Address"],
    discounts: Optional[Iterable[DiscountInfo]] = None,
) -> "TaxedMoney":
    total = (
        checkout_total(
            manager=manager,
            checkout=checkout,
            lines=lines,
            address=address,
            discounts=discounts,
        )
        - checkout.get_total_gift_cards_balance()
    )

    return max(total, zero_taxed_money(total.currency))


def checkout_total(
    *,
    manager: "PluginsManager",
    checkout: "Checkout",
    lines: Iterable["CheckoutLineInfo"],
    address: Optional["Address"],
    discounts: Optional[Iterable[DiscountInfo]] = None,
) -> "TaxedMoney":
    """Return the total cost of the checkout.

    Total is a cost of all lines and shipping fees, minus checkout discounts,
    taxes included.

    It takes in account all plugins.
    """
    calculated_checkout_total = manager.calculate_checkout_total(
        checkout, lines, address, discounts or []
    )
    return quantize_price(calculated_checkout_total, checkout.currency)


def checkout_line_total(
    *,
    manager: "PluginsManager",
    checkout: "Checkout",
    line: "CheckoutLine",  # FIXME: convert to CheckoutLineInfo
    variant: "ProductVariant",
    product: "Product",
    collections: Iterable["Collection"],
    address: Optional["Address"],
    channel: "Channel",
    channel_listing: "ProductVariantChannelListing",
    discounts: Optional[Iterable[DiscountInfo]] = None,
) -> "TaxedMoney":
    """Return the total price of provided line, taxes included.

    It takes in account all plugins.
    """
    calculated_line_total = manager.calculate_checkout_line_total(
        checkout,
        line,
        variant,
        product,
        collections,
        address,
        channel,
        channel_listing,
        discounts or [],
    )
    return quantize_price(calculated_line_total, line.checkout.currency)
