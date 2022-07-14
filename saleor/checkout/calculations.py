from decimal import Decimal
from typing import TYPE_CHECKING, Iterable, Optional, Tuple

from django.conf import settings
from django.utils import timezone
from prices import Money, TaxedMoney

from ..core.prices import quantize_price
from ..core.taxes import TaxData, zero_taxed_money
from ..discount import DiscountInfo
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
    currency = checkout_info.checkout.currency
    checkout_info, _ = fetch_checkout_prices_if_expired(
        checkout_info,
        manager=manager,
        lines=lines,
        address=address,
        discounts=discounts,
    )
    return quantize_price(checkout_info.checkout.shipping_price, currency)


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
    currency = checkout_info.checkout.currency
    checkout_info, _ = fetch_checkout_prices_if_expired(
        checkout_info,
        manager=manager,
        lines=lines,
        address=address,
        discounts=discounts,
    )
    return quantize_price(checkout_info.checkout.subtotal, currency)


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
    currency = checkout_info.checkout.currency
    checkout_info, _ = fetch_checkout_prices_if_expired(
        checkout_info,
        manager=manager,
        lines=lines,
        address=address,
        discounts=discounts,
    )
    return quantize_price(checkout_info.checkout.total, currency)


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
) -> TaxedMoney:
    """Return the total price of provided line, taxes included.

    It takes in account all plugins.
    """
    currency = checkout_info.checkout.currency
    address = checkout_info.shipping_address or checkout_info.billing_address
    _, lines = fetch_checkout_prices_if_expired(
        checkout_info,
        manager=manager,
        lines=lines,
        address=address,
        discounts=discounts,
    )
    checkout_line = _find_checkout_line_info(lines, checkout_line_info).line
    return quantize_price(checkout_line.total_price, currency)


def checkout_line_unit_price(
    *,
    manager: "PluginsManager",
    checkout_info: "CheckoutInfo",
    lines: Iterable["CheckoutLineInfo"],
    checkout_line_info: "CheckoutLineInfo",
    discounts: Iterable[DiscountInfo],
) -> TaxedMoney:
    """Return the unit price of provided line, taxes included.

    It takes in account all plugins.
    """
    currency = checkout_info.checkout.currency
    address = checkout_info.shipping_address or checkout_info.billing_address
    _, lines = fetch_checkout_prices_if_expired(
        checkout_info,
        manager=manager,
        lines=lines,
        address=address,
        discounts=discounts,
    )
    checkout_line = _find_checkout_line_info(lines, checkout_line_info).line
    unit_price = checkout_line.total_price / checkout_line.quantity
    return quantize_price(unit_price, currency)


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

    # Taxes are applied to the discounted prices
    _apply_tax_data_from_plugins(
        checkout, manager, checkout_info, lines, address, discounts
    )

    tax_data = manager.get_taxes_for_checkout(
        checkout_info,
        lines,
    )
    if tax_data:
        _apply_tax_data_from_app(checkout, lines, tax_data)

    checkout.price_expiration = (
        timezone.now() + settings.CHECKOUT_PRICES_TTL  # type: ignore
    )
    checkout.save(
        update_fields=[
            "voucher_code",
            "total_net_amount",
            "total_gross_amount",
            "subtotal_net_amount",
            "subtotal_gross_amount",
            "shipping_price_net_amount",
            "shipping_price_gross_amount",
            "shipping_tax_rate",
            "price_expiration",
            "translated_discount_name",
            "discount_amount",
            "discount_name",
            "currency",
        ],
        using=settings.DATABASE_CONNECTION_DEFAULT_NAME,
    )

    checkout.lines.bulk_update(
        [line_info.line for line_info in lines],
        [
            "total_price_net_amount",
            "total_price_gross_amount",
            "tax_rate",
        ],
    )

    return checkout_info, lines


def _calculate_checkout_total(checkout, currency):
    total = checkout.subtotal + checkout.shipping_price
    return quantize_price(
        total,
        currency,
    )


def _calculate_checkout_subtotal(lines, currency):
    line_totals = [line_info.line.total_price for line_info in lines]
    total = sum(line_totals, zero_taxed_money(currency))
    return quantize_price(
        total,
        currency,
    )


def _apply_tax_data_from_app(
    checkout: "Checkout", lines: Iterable["CheckoutLineInfo"], tax_data: TaxData
) -> None:
    currency = checkout.currency
    for (line_info, tax_line_data) in zip(lines, tax_data.lines):
        line = line_info.line

        line.total_price = quantize_price(
            TaxedMoney(
                net=Money(tax_line_data.total_net_amount, currency),
                gross=Money(tax_line_data.total_gross_amount, currency),
            ),
            currency,
        )
        # We use % value in tax app input but on database we store
        # it as a fractional value.
        # e.g Tax app sends `10%` as `10` but in database it's stored as `0.1`
        line.tax_rate = tax_line_data.tax_rate / 100

    # We use % value in tax app input but on database we store it as a fractional value.
    # e.g Tax app sends `10%` as `10` but in database it's stored as `0.1`
    checkout.shipping_tax_rate = tax_data.shipping_tax_rate / 100
    checkout.shipping_price = quantize_price(
        TaxedMoney(
            net=Money(tax_data.shipping_price_net_amount, currency),
            gross=Money(tax_data.shipping_price_gross_amount, currency),
        ),
        currency,
    )
    checkout.subtotal = _calculate_checkout_subtotal(lines, currency)
    checkout.total = _calculate_checkout_total(checkout, currency)


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

        total_price = manager.calculate_checkout_line_total(
            checkout_info,
            lines,
            line_info,
            address,
            discounts,
        )
        line.total_price = total_price

        unit_price = manager.calculate_checkout_line_unit_price(
            checkout_info,
            lines,
            line_info,
            address,
            discounts,
        )

        line.tax_rate = manager.get_checkout_line_tax_rate(
            checkout_info,
            lines,
            line_info,
            address,
            discounts,
            unit_price,
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
