from typing import TYPE_CHECKING, Iterable, Optional

from django.conf import settings
from django.utils import timezone

from ..core.prices import quantize_price
from ..core.taxes import TaxData, TaxError, TaxLineData, zero_taxed_money
from ..discount import DiscountInfo
from .models import Checkout, CheckoutLine

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
    address: Optional["Address"] = None,
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
    address: Optional["Address"] = None,
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
    address: Optional["Address"] = None,
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
    address: Optional["Address"] = None,
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
    discounts: Optional[Iterable[DiscountInfo]] = None,
) -> "TaxedMoney":
    """Return the total price of provided line, taxes included.

    It takes in account all plugins.
    """
    address = checkout_info.shipping_address or checkout_info.billing_address
    calculated_line_total = manager.calculate_checkout_line_total(
        checkout_info,
        lines,
        checkout_line_info,
        address,
        discounts or [],
    )
    return quantize_price(calculated_line_total, checkout_info.checkout.currency)


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

    plugins_tax_data = _get_tax_data_from_plugins(
        checkout, manager, checkout_info, lines, address, discounts
    )

    webhooks_tax_data = manager.get_taxes_for_checkout(checkout)

    if webhooks_tax_data:
        _apply_tax_data(checkout, webhooks_tax_data)
    elif plugins_tax_data:
        _apply_tax_data(checkout, plugins_tax_data)

    return checkout


def _apply_tax_data(checkout: "Checkout", tax_data: TaxData) -> None:
    def QP(price):
        return quantize_price(price, checkout.currency)

    checkout.total_net_amount = QP(tax_data.total_net_amount)
    checkout.total_gross_amount = QP(tax_data.total_gross_amount)

    checkout.subtotal_net_amount = QP(tax_data.subtotal_net_amount)
    checkout.subtotal_gross_amount = QP(tax_data.subtotal_gross_amount)

    checkout.shipping_price_net_amount = QP(tax_data.shipping_price_net_amount)
    checkout.shipping_price_gross_amount = QP(tax_data.shipping_price_gross_amount)

    checkout.price_expiration += settings.CHECKOUT_PRICES_TTL
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

    checkout_lines = checkout.lines.all()

    for (checkout_line, tax_line_data) in zip(checkout_lines, tax_data.lines):
        checkout_line.unit_price_net_amount = QP(tax_line_data.unit_net_amount)
        checkout_line.unit_price_gross_amount = QP(tax_line_data.unit_gross_amount)

        checkout_line.total_price_net_amount = QP(tax_line_data.total_net_amount)
        checkout_line.total_price_gross_amount = QP(tax_line_data.total_gross_amount)

    CheckoutLine.objects.bulk_update(
        checkout_lines,
        [
            "unit_price_net_amount",
            "unit_price_gross_amount",
            "total_price_net_amount",
            "total_price_gross_amount",
        ],
    )


def _get_tax_data_from_plugins(
    checkout: "Checkout",
    manager: "PluginsManager",
    checkout_info: "CheckoutInfo",
    lines: Iterable["CheckoutLineInfo"],
    address: Optional["Address"],
    discounts: Optional[Iterable[DiscountInfo]] = None,
) -> Optional[TaxData]:
    def get_line_total_price(line_info: "CheckoutLineInfo") -> "TaxedMoney":
        return manager.calculate_checkout_line_total(
            checkout_info,
            lines,
            line_info,
            address,
            discounts or [],
        )

    def get_line_unit_price(
        total: "TaxedMoney", line: CheckoutLine, line_info: "CheckoutLineInfo"
    ) -> "TaxedMoney":
        return manager.calculate_checkout_line_unit_price(
            total,
            line.quantity,
            checkout_info,
            lines,
            line_info,
            address,
            discounts or [],
        )

    try:
        tax_lines = [
            TaxLineData(
                id=0,
                currency=checkout.currency,
                total_net_amount=(
                    total_price := get_line_total_price(line_info)
                ).net.amount,
                total_gross_amount=total_price.gross.amount,
                unit_net_amount=(
                    unit_price := get_line_unit_price(total_price, line, line_info)
                ).net.amount,
                unit_gross_amount=unit_price.gross.amount,
            )
            for (line, line_info) in zip(checkout.lines.all(), lines)
        ]

        shipping_price = manager.calculate_checkout_shipping(
            checkout_info, lines, address, discounts or []
        )
        subtotal = manager.calculate_checkout_subtotal(
            checkout_info, lines, address, discounts or []
        )
        total = manager.calculate_checkout_total(
            checkout_info, lines, address, discounts or []
        )

        return TaxData(
            currency=checkout.currency,
            total_net_amount=total.net.amount,
            total_gross_amount=total.gross.amount,
            subtotal_net_amount=subtotal.net.amount,
            subtotal_gross_amount=subtotal.gross.amount,
            shipping_price_net_amount=shipping_price.net.amount,
            shipping_price_gross_amount=shipping_price.gross.amount,
            lines=tax_lines,
        )
    except TaxError:
        return None
