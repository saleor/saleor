import logging
from collections.abc import Iterable
from decimal import Decimal
from typing import TYPE_CHECKING, Optional, cast

from django.conf import settings
from django.utils import timezone
from prices import Money, TaxedMoney

from ..checkout import base_calculations
from ..core.db.connection import allow_writer
from ..core.prices import quantize_price
from ..core.taxes import TaxData, TaxEmptyData, zero_money, zero_taxed_money
from ..discount.utils.checkout import (
    create_or_update_discount_objects_from_promotion_for_checkout,
)
from ..payment.models import TransactionItem
from ..plugins import PLUGIN_IDENTIFIER_PREFIX
from ..tax import TaxCalculationStrategy
from ..tax.calculations.checkout import update_checkout_prices_with_flat_rates
from ..tax.utils import (
    get_charge_taxes_for_checkout,
    get_tax_app_identifier_for_checkout,
    get_tax_calculation_strategy_for_checkout,
    normalize_tax_rate_for_db,
)
from .fetch import find_checkout_line_info
from .models import Checkout
from .payment_utils import update_checkout_payment_statuses

if TYPE_CHECKING:
    from ..account.models import Address
    from ..plugins.manager import PluginsManager
    from .fetch import CheckoutInfo, CheckoutLineInfo

logger = logging.getLogger(__name__)


def checkout_shipping_price(
    *,
    manager: "PluginsManager",
    checkout_info: "CheckoutInfo",
    lines: Iterable["CheckoutLineInfo"],
    address: Optional["Address"],
    database_connection_name: str = settings.DATABASE_CONNECTION_DEFAULT_NAME,
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
        database_connection_name=database_connection_name,
    )
    return quantize_price(checkout_info.checkout.shipping_price, currency)


def checkout_shipping_tax_rate(
    *,
    manager: "PluginsManager",
    checkout_info: "CheckoutInfo",
    lines: Iterable["CheckoutLineInfo"],
    address: Optional["Address"],
    database_connection_name: str = settings.DATABASE_CONNECTION_DEFAULT_NAME,
) -> Decimal:
    """Return checkout shipping tax rate.

    It takes in account all plugins.
    """
    checkout_info, _ = fetch_checkout_data(
        checkout_info,
        manager=manager,
        lines=lines,
        address=address,
        database_connection_name=database_connection_name,
    )
    return checkout_info.checkout.shipping_tax_rate


def checkout_subtotal(
    *,
    manager: "PluginsManager",
    checkout_info: "CheckoutInfo",
    lines: Iterable["CheckoutLineInfo"],
    address: Optional["Address"],
    database_connection_name: str = settings.DATABASE_CONNECTION_DEFAULT_NAME,
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
        database_connection_name=database_connection_name,
    )
    return quantize_price(checkout_info.checkout.subtotal, currency)


def calculate_checkout_total_with_gift_cards(
    manager: "PluginsManager",
    checkout_info: "CheckoutInfo",
    lines: Iterable["CheckoutLineInfo"],
    address: Optional["Address"],
    database_connection_name: str = settings.DATABASE_CONNECTION_DEFAULT_NAME,
) -> "TaxedMoney":
    total = checkout_total(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        address=address,
        database_connection_name=database_connection_name,
    ) - checkout_info.checkout.get_total_gift_cards_balance(database_connection_name)

    return max(total, zero_taxed_money(total.currency))


def checkout_total(
    *,
    manager: "PluginsManager",
    checkout_info: "CheckoutInfo",
    lines: Iterable["CheckoutLineInfo"],
    address: Optional["Address"],
    database_connection_name: str = settings.DATABASE_CONNECTION_DEFAULT_NAME,
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
        database_connection_name=database_connection_name,
    )
    return quantize_price(checkout_info.checkout.total, currency)


def checkout_line_total(
    *,
    manager: "PluginsManager",
    checkout_info: "CheckoutInfo",
    lines: Iterable["CheckoutLineInfo"],
    checkout_line_info: "CheckoutLineInfo",
    database_connection_name: str = settings.DATABASE_CONNECTION_DEFAULT_NAME,
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
        database_connection_name=database_connection_name,
    )
    checkout_line = find_checkout_line_info(lines, checkout_line_info.line.id).line
    return quantize_price(checkout_line.total_price, currency)


def checkout_line_unit_price(
    *,
    manager: "PluginsManager",
    checkout_info: "CheckoutInfo",
    lines: Iterable["CheckoutLineInfo"],
    checkout_line_info: "CheckoutLineInfo",
    database_connection_name: str = settings.DATABASE_CONNECTION_DEFAULT_NAME,
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
        database_connection_name=database_connection_name,
    )
    checkout_line = find_checkout_line_info(lines, checkout_line_info.line.id).line
    unit_price = checkout_line.total_price / checkout_line.quantity
    return quantize_price(unit_price, currency)


def checkout_line_tax_rate(
    *,
    manager: "PluginsManager",
    checkout_info: "CheckoutInfo",
    lines: Iterable["CheckoutLineInfo"],
    checkout_line_info: "CheckoutLineInfo",
    database_connection_name: str = settings.DATABASE_CONNECTION_DEFAULT_NAME,
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
        database_connection_name=database_connection_name,
    )
    checkout_line_info = find_checkout_line_info(lines, checkout_line_info.line.id)
    return checkout_line_info.line.tax_rate


def _fetch_checkout_prices_if_expired(
    checkout_info: "CheckoutInfo",
    manager: "PluginsManager",
    lines: Iterable["CheckoutLineInfo"],
    address: Optional["Address"] = None,
    force_update: bool = False,
    database_connection_name: str = settings.DATABASE_CONNECTION_DEFAULT_NAME,
) -> tuple["CheckoutInfo", Iterable["CheckoutLineInfo"]]:
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
        checkout_info, lines, database_connection_name=database_connection_name
    )
    prices_entered_with_tax = tax_configuration.prices_entered_with_tax
    charge_taxes = get_charge_taxes_for_checkout(
        checkout_info, lines, database_connection_name=database_connection_name
    )
    should_charge_tax = charge_taxes and not checkout.tax_exemption
    tax_app_identifier = get_tax_app_identifier_for_checkout(
        checkout_info, lines, database_connection_name
    )

    lines = cast(list, lines)
    create_or_update_discount_objects_from_promotion_for_checkout(
        checkout_info, lines, database_connection_name
    )

    checkout.tax_error = None
    if prices_entered_with_tax:
        # If prices are entered with tax, we need to always calculate it anyway, to
        # display the tax rate to the user.
        try:
            _calculate_and_add_tax(
                tax_calculation_strategy,
                tax_app_identifier,
                checkout,
                manager,
                checkout_info,
                lines,
                prices_entered_with_tax,
                address,
                database_connection_name=database_connection_name,
            )
        except TaxEmptyData as e:
            _set_checkout_base_prices(checkout, checkout_info, lines)
            checkout.tax_error = str(e)

        if not should_charge_tax:
            # If charge_taxes is disabled or checkout is exempt from taxes, remove the
            # tax from the original gross prices.
            _remove_tax(checkout, lines)

    else:
        # Prices are entered without taxes.
        if should_charge_tax:
            # Calculate taxes if charge_taxes is enabled and checkout is not exempt
            # from taxes.
            try:
                _calculate_and_add_tax(
                    tax_calculation_strategy,
                    tax_app_identifier,
                    checkout,
                    manager,
                    checkout_info,
                    lines,
                    prices_entered_with_tax,
                    address,
                    database_connection_name=database_connection_name,
                )
            except TaxEmptyData as e:
                _set_checkout_base_prices(checkout, checkout_info, lines)
                checkout.tax_error = str(e)
        else:
            # Calculate net prices without taxes.
            _set_checkout_base_prices(checkout, checkout_info, lines)

    checkout_update_fields = [
        "voucher_code",
        "total_net_amount",
        "total_gross_amount",
        "subtotal_net_amount",
        "subtotal_gross_amount",
        "shipping_price_net_amount",
        "shipping_price_gross_amount",
        "shipping_tax_rate",
        "translated_discount_name",
        "discount_amount",
        "discount_name",
        "currency",
        "last_change",
        "price_expiration",
        "tax_error",
    ]

    checkout.price_expiration = timezone.now() + settings.CHECKOUT_PRICES_TTL

    with allow_writer():
        checkout.save(
            update_fields=checkout_update_fields,
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
    tax_app_identifier: Optional[str],
    checkout: "Checkout",
    manager: "PluginsManager",
    checkout_info: "CheckoutInfo",
    lines: Iterable["CheckoutLineInfo"],
    prices_entered_with_tax: bool,
    address: Optional["Address"] = None,
    database_connection_name: str = settings.DATABASE_CONNECTION_DEFAULT_NAME,
):
    from .utils import log_address_if_validation_skipped_for_checkout

    if tax_calculation_strategy == TaxCalculationStrategy.TAX_APP:
        # If taxAppId is not configured run all active plugins and tax apps.
        # If taxAppId is provided run tax plugin or Tax App. taxAppId can be
        # configured with Avatax plugin identifier.
        if not tax_app_identifier:
            # Call the tax plugins.
            _apply_tax_data_from_plugins(
                checkout, manager, checkout_info, lines, address
            )
            # Get the taxes calculated with apps and apply to checkout.
            tax_data = manager.get_taxes_for_checkout(
                checkout_info, lines, tax_app_identifier
            )
            if not tax_data:
                log_address_if_validation_skipped_for_checkout(checkout_info, logger)
            _apply_tax_data(checkout, lines, tax_data)
        else:
            _call_plugin_or_tax_app(
                tax_app_identifier,
                checkout,
                manager,
                checkout_info,
                lines,
                address,
            )
    else:
        # Get taxes calculated with flat rates and apply to checkout.
        update_checkout_prices_with_flat_rates(
            checkout,
            checkout_info,
            lines,
            prices_entered_with_tax,
            address,
            database_connection_name=database_connection_name,
        )


def _call_plugin_or_tax_app(
    tax_app_identifier: str,
    checkout: "Checkout",
    manager: "PluginsManager",
    checkout_info: "CheckoutInfo",
    lines: Iterable["CheckoutLineInfo"],
    address: Optional["Address"] = None,
):
    from .utils import log_address_if_validation_skipped_for_checkout

    if tax_app_identifier.startswith(PLUGIN_IDENTIFIER_PREFIX):
        plugin_ids = [tax_app_identifier.replace(PLUGIN_IDENTIFIER_PREFIX, "")]
        plugins = manager.get_plugins(
            checkout_info.channel.slug,
            active_only=True,
            plugin_ids=plugin_ids,
        )
        if not plugins:
            raise TaxEmptyData("Empty tax data.")
        _apply_tax_data_from_plugins(
            checkout,
            manager,
            checkout_info,
            lines,
            address,
            plugin_ids=plugin_ids,
        )
        if checkout.tax_error:
            raise TaxEmptyData("Empty tax data.")
    else:
        tax_data = manager.get_taxes_for_checkout(
            checkout_info, lines, tax_app_identifier
        )
        if tax_data is None:
            log_address_if_validation_skipped_for_checkout(checkout_info, logger)
            raise TaxEmptyData("Empty tax data.")
        _apply_tax_data(checkout, lines, tax_data)


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
    plugin_ids: Optional[list[str]] = None,
) -> None:
    for line_info in lines:
        line = line_info.line

        total_price = manager.calculate_checkout_line_total(
            checkout_info,
            lines,
            line_info,
            address,
            plugin_ids=plugin_ids,
        )
        line.total_price = total_price

        line.tax_rate = manager.get_checkout_line_tax_rate(
            checkout_info,
            lines,
            line_info,
            address,
            total_price,
            plugin_ids=plugin_ids,
        )

    checkout.shipping_price = manager.calculate_checkout_shipping(
        checkout_info, lines, address, plugin_ids=plugin_ids
    )
    checkout.shipping_tax_rate = manager.get_checkout_shipping_tax_rate(
        checkout_info, lines, address, checkout.shipping_price, plugin_ids=plugin_ids
    )
    checkout.subtotal = manager.calculate_checkout_subtotal(
        checkout_info, lines, address, plugin_ids=plugin_ids
    )
    checkout.total = manager.calculate_checkout_total(
        checkout_info,
        lines,
        address,
        plugin_ids=plugin_ids,
    )


def _set_checkout_base_prices(
    checkout: "Checkout",
    checkout_info: "CheckoutInfo",
    lines: Iterable["CheckoutLineInfo"],
) -> None:
    currency = checkout_info.checkout.currency
    subtotal = zero_money(currency)

    for line_info in lines:
        line = line_info.line
        quantity = line.quantity

        unit_price = base_calculations.calculate_base_line_unit_price(line_info)
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
    database_connection_name: str = settings.DATABASE_CONNECTION_DEFAULT_NAME,
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
        database_connection_name=database_connection_name,
    )
    current_total_gross = checkout_info.checkout.total.gross
    if current_total_gross != previous_total_gross or force_status_update:
        update_checkout_payment_statuses(
            checkout=checkout_info.checkout,
            checkout_total_gross=current_total_gross,
            checkout_has_lines=bool(lines),
            checkout_transactions=checkout_transactions,
            database_connection_name=database_connection_name,
        )

    return checkout_info, lines
