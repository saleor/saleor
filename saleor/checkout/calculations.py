from typing import TYPE_CHECKING, Iterable, Optional

from django.conf import settings
from django.utils import timezone

from ..core.prices import quantize_price
from ..core.taxes import TaxData, zero_taxed_money
from ..discount import DiscountInfo
from .models import Checkout

if TYPE_CHECKING:
    from prices import TaxedMoney

    from ..account.models import Address
    from ..plugins.manager import PluginsManager
    from .fetch import CheckoutInfo, CheckoutLineInfo


def checkout_shipping_price(
    *,
    manager: "PluginsManager",
    checkout_info: "CheckoutInfo",
    lines: Iterable["CheckoutLineInfo"],
    address: Optional["Address"],
    discounts: Optional[Iterable[DiscountInfo]] = None,
) -> "TaxedMoney":
    """Return checkout shipping price.

    It takes in account all plugins.
    """
    return fetch_checkout_prices_if_expired(
        checkout_info,
        manager=manager,
        lines=lines,
        address=address,
        discounts=discounts,
    ).shipping_price


def checkout_subtotal(
    *,
    manager: "PluginsManager",
    checkout_info: "CheckoutInfo",
    lines: Iterable["CheckoutLineInfo"],
    address: Optional["Address"],
    discounts: Optional[Iterable[DiscountInfo]] = None,
) -> "TaxedMoney":
    """Return the total cost of all the checkout lines, taxes included.

    It takes in account all plugins.
    """
    return fetch_checkout_prices_if_expired(
        checkout_info,
        manager=manager,
        lines=lines,
        address=address,
        discounts=discounts,
    ).subtotal


def calculate_checkout_total_with_gift_cards(
    manager: "PluginsManager",
    checkout_info: "CheckoutInfo",
    lines: Iterable["CheckoutLineInfo"],
    address: Optional["Address"],
    discounts: Optional[Iterable[DiscountInfo]] = None,
) -> "TaxedMoney":
    total = (
        checkout_total(
            manager=manager,
            checkout_info=checkout_info,
            lines=lines,
            address=address,
            discounts=discounts,
        )
        - checkout_info.checkout.get_total_gift_cards_balance()
    )

    return max(total, zero_taxed_money(total.currency))


def checkout_total(
    *,
    manager: "PluginsManager",
    checkout_info: "CheckoutInfo",
    lines: Iterable["CheckoutLineInfo"],
    address: Optional["Address"],
    discounts: Optional[Iterable[DiscountInfo]] = None,
) -> "TaxedMoney":
    """Return the total cost of the checkout.

    Total is a cost of all lines and shipping fees, minus checkout discounts,
    taxes included.

    It takes in account all plugins.
    """
    return fetch_checkout_prices_if_expired(
        checkout_info,
        manager=manager,
        lines=lines,
        address=address,
        discounts=discounts,
    ).total


def checkout_line_total(
    *,
    manager: "PluginsManager",
    checkout_info: "CheckoutInfo",
    lines: Iterable["CheckoutLineInfo"],
    checkout_line_info: "CheckoutLineInfo",
    discounts: Iterable[DiscountInfo],
) -> "TaxedMoney":
    """Return the total price of provided line, taxes included.

    It takes in account all plugins.
    """
    address = checkout_info.shipping_address or checkout_info.billing_address
    return (
        fetch_checkout_prices_if_expired(
            checkout_info,
            manager=manager,
            lines=lines,
            address=address,
            discounts=discounts,
        )
        .lines.get(pk=checkout_line_info.line.pk)
        .total_price
    )


def checkout_line_unit_price(
    *,
    manager: "PluginsManager",
    checkout_info: "CheckoutInfo",
    lines: Iterable["CheckoutLineInfo"],
    checkout_line_info: "CheckoutLineInfo",
    discounts: Iterable[DiscountInfo],
) -> "TaxedMoney":
    address = checkout_info.shipping_address or checkout_info.billing_address
    return (
        fetch_checkout_prices_if_expired(
            checkout_info,
            manager=manager,
            lines=lines,
            address=address,
            discounts=discounts,
        )
        .lines.get(pk=checkout_line_info.line.pk)
        .unit_price
    )


def fetch_checkout_prices_if_expired(
    checkout_info: "CheckoutInfo",
    manager: "PluginsManager",
    lines: Iterable["CheckoutLineInfo"],
    address: Optional["Address"] = None,
    discounts: Optional[Iterable["DiscountInfo"]] = None,
    force_update: bool = False,
) -> "Checkout":
    checkout = checkout_info.checkout

    if not force_update and checkout.price_expiration < timezone.now():
        return checkout

    _apply_tax_data_from_plugins(
        checkout, manager, checkout_info, lines, address, discounts
    )

    tax_data = manager.get_taxes_for_checkout(checkout)

    if tax_data:
        _apply_tax_data(checkout, lines, tax_data)

    checkout.price_expiration = timezone.now() + settings.CHECKOUT_PRICES_TTL
    checkout.save(
        update_fields=[
            "total_net_amount",
            "total_gross_amount",
            "subtotal_net_amount",
            "subtotal_gross_amount",
            "shipping_price_net_amount",
            "shipping_price_gross_amount",
            "price_expiration",
        ]
    )

    checkout.lines.bulk_update(
        [line_info.line for line_info in lines],
        [
            "unit_price_net_amount",
            "unit_price_gross_amount",
            "total_price_net_amount",
            "total_price_gross_amount",
        ],
    )

    return checkout


def _apply_tax_data(
    checkout: "Checkout", lines: Iterable["CheckoutLineInfo"], tax_data: TaxData
) -> None:
    def qp(price):
        return quantize_price(price, checkout.currency)

    checkout.total_net_amount = tax_data.total_net_amount
    checkout.total_gross_amount = tax_data.total_gross_amount
    checkout.total = qp(checkout.total)

    checkout.subtotal_net_amount = tax_data.subtotal_net_amount
    checkout.subtotal_gross_amount = tax_data.subtotal_gross_amount
    checkout.subtotal = qp(checkout.subtotal)

    checkout.shipping_price_net_amount = tax_data.shipping_price_net_amount
    checkout.shipping_price_gross_amount = tax_data.shipping_price_gross_amount
    checkout.shipping_price = qp(checkout.shipping_price)

    for (line_info, tax_line_data) in zip(lines, tax_data.lines):
        line = line_info.line

        line.unit_price_net_amount = tax_line_data.unit_net_amount
        line.unit_price_gross_amount = tax_line_data.unit_gross_amount
        line.unit_price = qp(line.unit_price)

        line.total_price_net_amount = tax_line_data.total_net_amount
        line.total_price_gross_amount = tax_line_data.total_gross_amount
        line.total_price = qp(line.total_price)


def _apply_tax_data_from_plugins(
    checkout: "Checkout",
    manager: "PluginsManager",
    checkout_info: "CheckoutInfo",
    lines: Iterable["CheckoutLineInfo"],
    address: Optional["Address"],
    discounts: Optional[Iterable[DiscountInfo]] = None,
) -> None:
    for line_info in lines:
        line_info.line.total_price = manager.calculate_checkout_line_total(
            checkout_info,
            lines,
            line_info,
            address,
            discounts or [],
        )
        line_info.line.unit_price = manager.calculate_checkout_line_unit_price(
            line_info.line.total_price,
            line_info.line.quantity,
            checkout_info,
            lines,
            line_info,
            address,
            discounts or [],
        )

    checkout.shipping_price = manager.calculate_checkout_shipping(
        checkout_info, lines, address, discounts or []
    )
    checkout.subtotal = manager.calculate_checkout_subtotal(
        checkout_info, lines, address, discounts or []
    )
    checkout.total = manager.calculate_checkout_total(
        checkout_info, lines, address, discounts or []
    )
