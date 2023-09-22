from decimal import Decimal
from typing import TYPE_CHECKING, Iterable, Optional, Tuple

from django.conf import settings
from django.utils import timezone
from prices import Money, TaxedMoney

from ..checkout import base_calculations
from ..core.prices import quantize_price
from ..core.taxes import TaxData, zero_money, zero_taxed_money
from ..discount.utils import generate_sale_discount_objects_for_checkout
from ..payment.models import TransactionItem
from ..tax import TaxCalculationStrategy
from ..tax.calculations.checkout import update_checkout_prices_with_flat_rates
from ..tax.utils import (
    get_charge_taxes_for_checkout,
    get_tax_calculation_strategy_for_checkout,
    normalize_tax_rate_for_db,
)
from .models import Checkout
from .payment_utils import update_checkout_payment_statuses

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
) -> "TaxedMoney":
    """Return checkout shipping price.

    It takes in account all plugins.
    """
    currency = checkout_info.checkout.currency
    checkout_info, _ = fetch_checkout_data(
        checkout_info,
        manager=manager,
        lines=lines,
        address=address,
    )
    return quantize_price(checkout_info.checkout.shipping_price, currency)


def checkout_shipping_tax_rate(
    *,
    manager: "PluginsManager",
    checkout_info: "CheckoutInfo",
    lines: Iterable["CheckoutLineInfo"],
    address: Optional["Address"],
) -> Decimal:
    """Return checkout shipping tax rate.

    It takes in account all plugins.
    """
    checkout_info, _ = fetch_checkout_data(
        checkout_info,
        manager=manager,
        lines=lines,
        address=address,
    )
    return checkout_info.checkout.shipping_tax_rate


def checkout_subtotal(
    *,
    manager: "PluginsManager",
    checkout_info: "CheckoutInfo",
    lines: Iterable["CheckoutLineInfo"],
    address: Optional["Address"],
) -> "TaxedMoney":
    """Return the total cost of all the checkout lines, taxes included.

    It takes in account all plugins.
    """
    currency = checkout_info.checkout.currency
    checkout_info, _ = fetch_checkout_data(
        checkout_info,
        manager=manager,
        lines=lines,
        address=address,
    )
    return quantize_price(checkout_info.checkout.subtotal, currency)


def calculate_checkout_total_with_gift_cards(
    manager: "PluginsManager",
    checkout_info: "CheckoutInfo",
    lines: Iterable["CheckoutLineInfo"],
    address: Optional["Address"],
) -> "TaxedMoney":
    total = (
        checkout_total(
            manager=manager,
            checkout_info=checkout_info,
            lines=lines,
            address=address,
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
) -> "TaxedMoney":
    """Return the total cost of the checkout.

    Total is a cost of all lines and shipping fees, minus checkout discounts,
    taxes included.

    It takes in account all plugins.
    """
    currency = checkout_info.checkout.currency
    checkout_info, _ = fetch_checkout_data(
        checkout_info,
        manager=manager,
        lines=lines,
        address=address,
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
) -> TaxedMoney:
    """Return the total price of provided line, taxes included.

    It takes in account all plugins.
    """
    currency = checkout_info.checkout.currency
    address = checkout_info.shipping_address or checkout_info.billing_address
    _, lines = fetch_checkout_data(
        checkout_info,
        manager=manager,
        lines=lines,
        address=address,
    )
    checkout_line = _find_checkout_line_info(lines, checkout_line_info).line
    return quantize_price(checkout_line.total_price, currency)


def checkout_line_unit_price(
    *,
    manager: "PluginsManager",
    checkout_info: "CheckoutInfo",
    lines: Iterable["CheckoutLineInfo"],
    checkout_line_info: "CheckoutLineInfo",
) -> TaxedMoney:
    """Return the unit price of provided line, taxes included.

    It takes in account all plugins.
    """
    currency = checkout_info.checkout.currency
    address = checkout_info.shipping_address or checkout_info.billing_address
    _, lines = fetch_checkout_data(
        checkout_info,
        manager=manager,
        lines=lines,
        address=address,
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
) -> Decimal:
    """Return the tax rate of provided line.

    It takes in account all plugins.
    """
    address = checkout_info.shipping_address or checkout_info.billing_address
    _, lines = fetch_checkout_data(
        checkout_info,
        manager=manager,
        lines=lines,
        address=address,
    )
    checkout_line_info = _find_checkout_line_info(lines, checkout_line_info)
    return checkout_line_info.line.tax_rate


def _fetch_checkout_prices_if_expired(
    checkout_info: "CheckoutInfo",
    manager: "PluginsManager",
    lines: Iterable["CheckoutLineInfo"],
    address: Optional["Address"] = None,
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

    tax_configuration = checkout_info.tax_configuration
    tax_calculation_strategy = get_tax_calculation_strategy_for_checkout(
        checkout_info, lines
    )
    prices_entered_with_tax = tax_configuration.prices_entered_with_tax
    charge_taxes = get_charge_taxes_for_checkout(checkout_info, lines)
    should_charge_tax = charge_taxes and not checkout.tax_exemption

    generate_sale_discount_objects_for_checkout(checkout_info, lines)

    if prices_entered_with_tax:
        # If prices are entered with tax, we need to always calculate it anyway, to
        # display the tax rate to the user.
        _calculate_and_add_tax(
            tax_calculation_strategy,
            checkout,
            manager,
            checkout_info,
            lines,
            prices_entered_with_tax,
            address,
        )

        if not should_charge_tax:
            # If charge_taxes is disabled or checkout is exempt from taxes, remove the
            # tax from the original gross prices.
            _remove_tax(checkout, lines)

    else:
        # Prices are entered without taxes.
        if should_charge_tax:
            # Calculate taxes if charge_taxes is enabled and checkout is not exempt
            # from taxes.
            _calculate_and_add_tax(
                tax_calculation_strategy,
                checkout,
                manager,
                checkout_info,
                lines,
                prices_entered_with_tax,
                address,
            )
        else:
            # Calculate net prices without taxes.
            _get_checkout_base_prices(checkout, checkout_info, lines)

    checkout.price_expiration = timezone.now() + settings.CHECKOUT_PRICES_TTL
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
            "last_change",
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


def _calculate_and_add_tax(
    tax_calculation_strategy: str,
    checkout: "Checkout",
    manager: "PluginsManager",
    checkout_info: "CheckoutInfo",
    lines: Iterable["CheckoutLineInfo"],
    prices_entered_with_tax: bool,
    address: Optional["Address"] = None,
):
    if tax_calculation_strategy == TaxCalculationStrategy.TAX_APP:
        # Call the tax plugins.
        _apply_tax_data_from_plugins(checkout, manager, checkout_info, lines, address)
        # Get the taxes calculated with apps and apply to checkout.
        tax_data = manager.get_taxes_for_checkout(checkout_info, lines)
        _apply_tax_data(checkout, lines, tax_data)
    else:
        # Get taxes calculated with flat rates and apply to checkout.
        update_checkout_prices_with_flat_rates(
            checkout, checkout_info, lines, prices_entered_with_tax, address
        )


def _remove_tax(checkout, lines_info):
    checkout.total_gross_amount = checkout.total_net_amount
    checkout.subtotal_gross_amount = checkout.subtotal_net_amount
    checkout.shipping_price_gross_amount = checkout.shipping_price_net_amount
    checkout.shipping_tax_rate = Decimal("0.00")

    for line_info in lines_info:
        total_price_net_amount = line_info.line.total_price_net_amount
        line_info.line.total_price_gross_amount = total_price_net_amount
        line_info.line.tax_rate = Decimal("0.00")


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


def _apply_tax_data(
    checkout: "Checkout",
    lines: Iterable["CheckoutLineInfo"],
    tax_data: Optional[TaxData],
) -> None:
    if not tax_data:
        return

    currency = checkout.currency
    for line_info, tax_line_data in zip(lines, tax_data.lines):
        line = line_info.line

        line.total_price = quantize_price(
            TaxedMoney(
                net=Money(tax_line_data.total_net_amount, currency),
                gross=Money(tax_line_data.total_gross_amount, currency),
            ),
            currency,
        )
        line.tax_rate = normalize_tax_rate_for_db(tax_line_data.tax_rate)

    checkout.shipping_tax_rate = normalize_tax_rate_for_db(tax_data.shipping_tax_rate)
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
) -> None:
    for line_info in lines:
        line = line_info.line

        total_price = manager.calculate_checkout_line_total(
            checkout_info,
            lines,
            line_info,
            address,
        )
        line.total_price = total_price

        line.tax_rate = manager.get_checkout_line_tax_rate(
            checkout_info,
            lines,
            line_info,
            address,
            total_price,
        )

    checkout.shipping_price = manager.calculate_checkout_shipping(
        checkout_info, lines, address
    )
    checkout.shipping_tax_rate = manager.get_checkout_shipping_tax_rate(
        checkout_info, lines, address, checkout.shipping_price
    )
    checkout.subtotal = manager.calculate_checkout_subtotal(
        checkout_info, lines, address
    )
    checkout.total = manager.calculate_checkout_total(checkout_info, lines, address)


def _get_checkout_base_prices(
    checkout: "Checkout",
    checkout_info: "CheckoutInfo",
    lines: Iterable["CheckoutLineInfo"],
) -> None:
    currency = checkout_info.checkout.currency
    subtotal = zero_money(currency)

    for line_info in lines:
        line = line_info.line
        quantity = line.quantity

        unit_price = base_calculations.calculate_base_line_unit_price(
            line_info, checkout_info.channel
        )
        total_price = base_calculations.apply_checkout_discount_on_checkout_line(
            checkout_info, lines, line_info, unit_price * quantity
        )
        line_total_price = quantize_price(total_price, currency)
        subtotal += line_total_price

        line.total_price = TaxedMoney(net=line_total_price, gross=line_total_price)

        # Set zero tax rate since net and gross are equal.
        line.tax_rate = Decimal("0.0")

    # Calculate shipping price
    shipping_price = base_calculations.base_checkout_delivery_price(
        checkout_info, lines
    )
    checkout.shipping_price = quantize_price(
        TaxedMoney(shipping_price, shipping_price), currency
    )
    checkout.shipping_tax_rate = Decimal("0.0")

    # Set subtotal
    checkout.subtotal = TaxedMoney(net=subtotal, gross=subtotal)

    # Calculate checkout total
    total = subtotal + shipping_price
    checkout.total = quantize_price(TaxedMoney(net=total, gross=total), currency)


def fetch_checkout_data(
    checkout_info: "CheckoutInfo",
    manager: "PluginsManager",
    lines: Iterable["CheckoutLineInfo"],
    address: Optional["Address"] = None,
    force_update: bool = False,
    checkout_transactions: Optional[Iterable["TransactionItem"]] = None,
    force_status_update: bool = False,
):
    """Fetch checkout data.

    This function refreshes prices if they have expired. If the checkout total has
    changed as a result, it will update the payment statuses accordingly.
    """
    previous_total_gross = checkout_info.checkout.total.gross
    checkout_info, lines = _fetch_checkout_prices_if_expired(
        checkout_info=checkout_info,
        manager=manager,
        lines=lines,
        address=address,
        force_update=force_update,
    )
    current_total_gross = checkout_info.checkout.total.gross
    if current_total_gross != previous_total_gross or force_status_update:
        update_checkout_payment_statuses(
            checkout=checkout_info.checkout,
            checkout_total_gross=current_total_gross,
            checkout_transactions=checkout_transactions,
        )

    return checkout_info, lines
