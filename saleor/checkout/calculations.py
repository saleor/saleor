from decimal import Decimal
from typing import TYPE_CHECKING, Iterable, Optional, Tuple

from django.conf import settings
from django.utils import timezone
from prices import Money, TaxedMoney

from ..core.prices import quantize_price
from ..core.taxes import TaxData, zero_taxed_money
from ..discount import DiscountInfo
from .interface import CheckoutTaxedPricesData
from .models import Checkout

if TYPE_CHECKING:

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
    checkout_info, _ = fetch_checkout_prices_if_expired(
        checkout_info,
        manager=manager,
        lines=lines,
        address=address,
        discounts=discounts,
    )
    return checkout_info.checkout.shipping_price


def checkout_shipping_tax_rate(
    *,
    manager: "PluginsManager",
    checkout_info: "CheckoutInfo",
    lines: Iterable["CheckoutLineInfo"],
    address: Optional["Address"],
    discounts: Optional[Iterable[DiscountInfo]] = None,
) -> Decimal:
    """Return checkout shipping tax rate.

    It takes in account all plugins.
    """
    checkout_info, _ = fetch_checkout_prices_if_expired(
        checkout_info,
        manager=manager,
        lines=lines,
        address=address,
        discounts=discounts,
    )
    return checkout_info.checkout.shipping_tax_rate


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
    checkout_info, _ = fetch_checkout_prices_if_expired(
        checkout_info,
        manager=manager,
        lines=lines,
        address=address,
        discounts=discounts,
    )
    return checkout_info.checkout.subtotal


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
    checkout_info, _ = fetch_checkout_prices_if_expired(
        checkout_info,
        manager=manager,
        lines=lines,
        address=address,
        discounts=discounts,
    )
    return checkout_info.checkout.total


def _find_checkout_line_info(
    lines: Iterable["CheckoutLineInfo"],
    checkout_line_info: "CheckoutLineInfo",
) -> "CheckoutLineInfo":
    """Return checkout line info from lines parameter.

    The return value represents the updated version of checkout_line_info parameter.
    """
    return next(
        line_info
        for line_info in lines
        if line_info.line.pk == checkout_line_info.line.pk
    )


def checkout_line_total(
    *,
    manager: "PluginsManager",
    checkout_info: "CheckoutInfo",
    lines: Iterable["CheckoutLineInfo"],
    checkout_line_info: "CheckoutLineInfo",
    discounts: Iterable[DiscountInfo] = [],
) -> "CheckoutTaxedPricesData":
    """Return the total price of provided line, taxes included.

    It takes in account all plugins.
    """
    address = checkout_info.shipping_address or checkout_info.billing_address
    _, lines = fetch_checkout_prices_if_expired(
        checkout_info,
        manager=manager,
        lines=lines,
        address=address,
        discounts=discounts,
    )
    checkout_line = _find_checkout_line_info(lines, checkout_line_info).line
    return CheckoutTaxedPricesData(
        undiscounted_price=checkout_line.undiscounted_total_price,
        price_with_sale=checkout_line.total_price,
        price_with_discounts=checkout_line.total_price_with_discounts,
    )


def checkout_line_unit_price(
    *,
    manager: "PluginsManager",
    checkout_info: "CheckoutInfo",
    lines: Iterable["CheckoutLineInfo"],
    checkout_line_info: "CheckoutLineInfo",
    discounts: Iterable[DiscountInfo],
) -> "CheckoutTaxedPricesData":
    """Return the unit price of provided line, taxes included.

    It takes in account all plugins.
    """
    address = checkout_info.shipping_address or checkout_info.billing_address
    _, lines = fetch_checkout_prices_if_expired(
        checkout_info,
        manager=manager,
        lines=lines,
        address=address,
        discounts=discounts,
    )
    checkout_line = _find_checkout_line_info(lines, checkout_line_info).line
    return CheckoutTaxedPricesData(
        undiscounted_price=checkout_line.undiscounted_unit_price,
        price_with_sale=checkout_line.unit_price,
        price_with_discounts=checkout_line.unit_price_with_discounts,
    )


def checkout_line_tax_rate(
    *,
    manager: "PluginsManager",
    checkout_info: "CheckoutInfo",
    lines: Iterable["CheckoutLineInfo"],
    checkout_line_info: "CheckoutLineInfo",
    discounts: Iterable[DiscountInfo],
) -> Decimal:
    """Return the tax rate of provided line.

    It takes in account all plugins.
    """
    address = checkout_info.shipping_address or checkout_info.billing_address
    _, lines = fetch_checkout_prices_if_expired(
        checkout_info,
        manager=manager,
        lines=lines,
        address=address,
        discounts=discounts,
    )
    checkout_line_info = _find_checkout_line_info(lines, checkout_line_info)
    return checkout_line_info.line.tax_rate


def force_taxes_recalculation(
    checkout_info: "CheckoutInfo",
    manager: "PluginsManager",
    lines: Iterable["CheckoutLineInfo"],
    address: Optional["Address"] = None,
    discounts: Optional[Iterable["DiscountInfo"]] = None,
) -> None:
    """Fetch checkout prices with taxes.

    Prices will be updated without taking into consideration price_expiration.
    """
    fetch_checkout_prices_if_expired(
        checkout_info, manager, lines, address, discounts, force_update=True
    )


def fetch_checkout_prices_if_expired(
    checkout_info: "CheckoutInfo",
    manager: "PluginsManager",
    lines: Iterable["CheckoutLineInfo"],
    address: Optional["Address"] = None,
    discounts: Optional[Iterable["DiscountInfo"]] = None,
    force_update: bool = False,
) -> Tuple["CheckoutInfo", Iterable["CheckoutLineInfo"]]:
    """Fetch checkout prices with taxes.

    First calculate and apply all checkout prices with taxes separately,
    then apply tax data as well if we receive one.

    Prices can be updated only if force_update == True, or if time elapsed from the
    last price update is greater than settings.CHECKOUT_PRICES_TTL.
    """
    checkout = checkout_info.checkout
    if not force_update and checkout.price_expiration > timezone.now():
        return checkout_info, lines

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
            "shipping_tax_rate",
            "price_expiration",
        ]
    )

    checkout.lines.bulk_update(
        [line_info.line for line_info in lines],
        [
            "unit_price_net_amount",
            "unit_price_gross_amount",
            "undiscounted_unit_price_net_amount",
            "undiscounted_unit_price_net_amount",
            "unit_price_with_discounts_gross_amount",
            "unit_price_with_discounts_gross_amount",
            "total_price_net_amount",
            "total_price_gross_amount",
            "undiscounted_total_price_net_amount",
            "undiscounted_total_price_net_amount",
            "total_price_with_discounts_gross_amount",
            "total_price_with_discounts_gross_amount",
            "tax_rate",
        ],
    )

    return checkout_info, lines


def _apply_tax_data(
    checkout: "Checkout", lines: Iterable["CheckoutLineInfo"], tax_data: TaxData
) -> None:
    def create_quantized_taxed_money(net: Decimal, gross: Decimal) -> TaxedMoney:
        currency = checkout.currency
        return quantize_price(
            TaxedMoney(net=Money(net, currency), gross=Money(gross, currency)), currency
        )

    checkout.total = create_quantized_taxed_money(
        net=tax_data.total_net_amount,
        gross=tax_data.total_gross_amount,
    )
    checkout.subtotal = create_quantized_taxed_money(
        net=tax_data.subtotal_net_amount, gross=tax_data.subtotal_gross_amount
    )
    checkout.shipping_price = create_quantized_taxed_money(
        net=tax_data.shipping_price_net_amount,
        gross=tax_data.shipping_price_gross_amount,
    )
    checkout.shipping_tax_rate = tax_data.shipping_tax_rate

    tax_lines_data = {
        tax_line_data.id: tax_line_data for tax_line_data in tax_data.lines
    }
    zipped_checkout_and_tax_lines = (
        (line_info, tax_lines_data[line_info.line.id]) for line_info in lines
    )

    for (line_info, tax_line_data) in zipped_checkout_and_tax_lines:
        line = line_info.line

        line.unit_price = create_quantized_taxed_money(
            net=tax_line_data.unit_net_amount, gross=tax_line_data.unit_gross_amount
        )
        line.total_price = create_quantized_taxed_money(
            net=tax_line_data.total_net_amount, gross=tax_line_data.total_gross_amount
        )
        line.tax_rate = tax_line_data.tax_rate


def _apply_tax_data_from_plugins(
    checkout: "Checkout",
    manager: "PluginsManager",
    checkout_info: "CheckoutInfo",
    lines: Iterable["CheckoutLineInfo"],
    address: Optional["Address"],
    discounts: Optional[Iterable[DiscountInfo]] = None,
) -> None:
    if not discounts:
        discounts = []

    for line_info in lines:
        line = line_info.line

        total_price_data = manager.calculate_checkout_line_total(
            checkout_info,
            lines,
            line_info,
            address,
            discounts,
        )
        line.undiscounted_total_price = total_price_data.undiscounted_price
        line.total_price = total_price_data.price_with_sale
        line.total_price_with_discounts = total_price_data.price_with_discounts

        unit_price_data = manager.calculate_checkout_line_unit_price(
            checkout_info,
            lines,
            line_info,
            address,
            discounts,
        )
        line.undiscounted_unit_price = unit_price_data.undiscounted_price
        line.unit_price = unit_price_data.price_with_sale
        line.unit_price_with_discounts = unit_price_data.price_with_discounts

        line.tax_rate = manager.get_checkout_line_tax_rate(
            checkout_info,
            lines,
            line_info,
            address,
            discounts,
            line.unit_price,
        )

    checkout.shipping_price = manager.calculate_checkout_shipping(
        checkout_info, lines, address, discounts
    )
    checkout.shipping_tax_rate = manager.get_checkout_shipping_tax_rate(
        checkout_info, lines, address, discounts, checkout.shipping_price
    )
    checkout.subtotal = manager.calculate_checkout_subtotal(
        checkout_info, lines, address, discounts
    )
    checkout.total = manager.calculate_checkout_total(
        checkout_info, lines, address, discounts
    )
