import logging
from collections.abc import Iterable
from decimal import Decimal
from typing import TYPE_CHECKING, Optional, cast

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from prices import Money, TaxedMoney

from ..core.db.connection import allow_writer
from ..core.prices import quantize_price
from ..core.taxes import (
    TaxData,
    TaxDataError,
    TaxDataErrorMessage,
    zero_money,
    zero_taxed_money,
)
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
from . import CheckoutAuthorizeStatus, base_calculations
from .fetch import find_checkout_line_info
from .lock_objects import checkout_qs_select_for_update
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
    lines: list["CheckoutLineInfo"],
    address: Optional["Address"],
    database_connection_name: str = settings.DATABASE_CONNECTION_DEFAULT_NAME,
    pregenerated_subscription_payloads: dict | None = None,
    allow_sync_webhooks: bool = True,
) -> "TaxedMoney":
    """Return checkout shipping price.

    It takes in account all plugins.
    """
    if pregenerated_subscription_payloads is None:
        pregenerated_subscription_payloads = {}
    currency = checkout_info.checkout.currency
    checkout_info, _ = fetch_checkout_data(
        checkout_info,
        manager=manager,
        lines=lines,
        database_connection_name=database_connection_name,
        pregenerated_subscription_payloads=pregenerated_subscription_payloads,
        allow_sync_webhooks=allow_sync_webhooks,
    )
    return quantize_price(checkout_info.checkout.shipping_price, currency)


def checkout_shipping_tax_rate(
    *,
    manager: "PluginsManager",
    checkout_info: "CheckoutInfo",
    lines: list["CheckoutLineInfo"],
    address: Optional["Address"],
    database_connection_name: str = settings.DATABASE_CONNECTION_DEFAULT_NAME,
    allow_sync_webhooks: bool = True,
) -> Decimal:
    """Return checkout shipping tax rate.

    It takes in account all plugins.
    """
    checkout_info, _ = fetch_checkout_data(
        checkout_info,
        manager=manager,
        lines=lines,
        database_connection_name=database_connection_name,
        allow_sync_webhooks=allow_sync_webhooks,
    )
    return checkout_info.checkout.shipping_tax_rate


def checkout_subtotal(
    *,
    manager: "PluginsManager",
    checkout_info: "CheckoutInfo",
    lines: list["CheckoutLineInfo"],
    address: Optional["Address"],
    database_connection_name: str = settings.DATABASE_CONNECTION_DEFAULT_NAME,
    pregenerated_subscription_payloads: dict | None = None,
    allow_sync_webhooks: bool = True,
) -> "TaxedMoney":
    """Return the total cost of all the checkout lines, taxes included.

    It takes in account all plugins.
    """
    if pregenerated_subscription_payloads is None:
        pregenerated_subscription_payloads = {}
    currency = checkout_info.checkout.currency
    checkout_info, _ = fetch_checkout_data(
        checkout_info,
        manager=manager,
        lines=lines,
        database_connection_name=database_connection_name,
        pregenerated_subscription_payloads=pregenerated_subscription_payloads,
        allow_sync_webhooks=allow_sync_webhooks,
    )
    return quantize_price(checkout_info.checkout.subtotal, currency)


def calculate_checkout_total_with_gift_cards(
    manager: "PluginsManager",
    checkout_info: "CheckoutInfo",
    lines: list["CheckoutLineInfo"],
    address: Optional["Address"],
    database_connection_name: str = settings.DATABASE_CONNECTION_DEFAULT_NAME,
    pregenerated_subscription_payloads: dict | None = None,
    force_update: bool = False,
    allow_sync_webhooks: bool = True,
) -> "TaxedMoney":
    """Return the total cost of the checkout taking into account gift cards total.

    Gift cards total is subtracted from total gross amount and subtracted proportionally
    from total net amount.
    """
    if pregenerated_subscription_payloads is None:
        pregenerated_subscription_payloads = {}
    total = calculate_checkout_total(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        address=address,
        database_connection_name=database_connection_name,
        pregenerated_subscription_payloads=pregenerated_subscription_payloads,
        force_update=force_update,
        allow_sync_webhooks=allow_sync_webhooks,
    )

    if total == zero_taxed_money(total.currency):
        return total

    # Calculate how many percent of total net value the total gross value is.
    gross_percentage = total.gross / total.net

    # Subtract gift cards value from total gross value.
    total.gross -= checkout_info.checkout.get_total_gift_cards_balance(
        database_connection_name
    )

    # Gross value cannot be below zero.
    total.gross = max(total.gross, zero_money(total.currency))

    # Adjusted total net value is proportional to potentially reduced total gross value.
    total.net = quantize_price(total.gross / gross_percentage, total.currency)

    return total


def calculate_checkout_total(
    *,
    manager: "PluginsManager",
    checkout_info: "CheckoutInfo",
    lines: list["CheckoutLineInfo"],
    address: Optional["Address"],
    database_connection_name: str = settings.DATABASE_CONNECTION_DEFAULT_NAME,
    pregenerated_subscription_payloads: dict | None = None,
    force_update: bool = False,
    allow_sync_webhooks: bool = True,
) -> "TaxedMoney":
    """Return the total cost of the checkout.

    Total is a cost of all lines and shipping fees, minus checkout discounts,
    taxes included.

    It takes in account all plugins.
    """
    if pregenerated_subscription_payloads is None:
        pregenerated_subscription_payloads = {}
    currency = checkout_info.checkout.currency
    checkout_info, _ = fetch_checkout_data(
        checkout_info,
        manager=manager,
        lines=lines,
        database_connection_name=database_connection_name,
        pregenerated_subscription_payloads=pregenerated_subscription_payloads,
        force_update=force_update,
        allow_sync_webhooks=allow_sync_webhooks,
    )
    return quantize_price(checkout_info.checkout.total, currency)


def checkout_line_total(
    *,
    manager: "PluginsManager",
    checkout_info: "CheckoutInfo",
    lines: list["CheckoutLineInfo"],
    checkout_line_info: "CheckoutLineInfo",
    database_connection_name: str = settings.DATABASE_CONNECTION_DEFAULT_NAME,
    pregenerated_subscription_payloads: dict | None = None,
    allow_sync_webhooks: bool = True,
) -> TaxedMoney:
    """Return the total price of provided line, taxes included.

    It takes in account all plugins.
    """
    if pregenerated_subscription_payloads is None:
        pregenerated_subscription_payloads = {}
    currency = checkout_info.checkout.currency
    _, lines = fetch_checkout_data(
        checkout_info,
        manager=manager,
        lines=lines,
        database_connection_name=database_connection_name,
        pregenerated_subscription_payloads=pregenerated_subscription_payloads,
        allow_sync_webhooks=allow_sync_webhooks,
    )
    checkout_line = find_checkout_line_info(lines, checkout_line_info.line.id).line
    return quantize_price(checkout_line.total_price, currency)


def checkout_line_unit_price(
    *,
    manager: "PluginsManager",
    checkout_info: "CheckoutInfo",
    lines: list["CheckoutLineInfo"],
    checkout_line_info: "CheckoutLineInfo",
    database_connection_name: str = settings.DATABASE_CONNECTION_DEFAULT_NAME,
    pregenerated_subscription_payloads: dict | None = None,
    allow_sync_webhooks: bool = True,
) -> TaxedMoney:
    """Return the unit price of provided line, taxes included.

    It takes in account all plugins.
    """
    if pregenerated_subscription_payloads is None:
        pregenerated_subscription_payloads = {}
    currency = checkout_info.checkout.currency
    _, lines = fetch_checkout_data(
        checkout_info,
        manager=manager,
        lines=lines,
        database_connection_name=database_connection_name,
        pregenerated_subscription_payloads=pregenerated_subscription_payloads,
        allow_sync_webhooks=allow_sync_webhooks,
    )
    checkout_line = find_checkout_line_info(lines, checkout_line_info.line.id).line
    unit_price = checkout_line.total_price / checkout_line.quantity
    return quantize_price(unit_price, currency)


def checkout_line_tax_rate(
    *,
    manager: "PluginsManager",
    checkout_info: "CheckoutInfo",
    lines: list["CheckoutLineInfo"],
    checkout_line_info: "CheckoutLineInfo",
    database_connection_name: str = settings.DATABASE_CONNECTION_DEFAULT_NAME,
    allow_sync_webhooks: bool = True,
) -> Decimal:
    """Return the tax rate of provided line.

    It takes in account all plugins.
    """
    _, lines = fetch_checkout_data(
        checkout_info,
        manager=manager,
        lines=lines,
        database_connection_name=database_connection_name,
        allow_sync_webhooks=allow_sync_webhooks,
    )
    checkout_line_info = find_checkout_line_info(lines, checkout_line_info.line.id)
    return checkout_line_info.line.tax_rate


def checkout_line_undiscounted_unit_price(
    *,
    checkout_info: "CheckoutInfo",
    checkout_line_info: "CheckoutLineInfo",
):
    # Fetch the undiscounted unit price from channel listings in case the prices
    # are invalidated.
    if checkout_info.checkout.price_expiration < timezone.now():
        return base_calculations.calculate_undiscounted_base_line_unit_price(
            checkout_line_info, checkout_info.channel
        )
    currency = checkout_info.checkout.currency
    return quantize_price(checkout_line_info.line.undiscounted_unit_price, currency)


def checkout_line_undiscounted_total_price(
    *,
    checkout_info: "CheckoutInfo",
    checkout_line_info: "CheckoutLineInfo",
):
    undiscounted_unit_price = checkout_line_undiscounted_unit_price(
        checkout_info=checkout_info, checkout_line_info=checkout_line_info
    )
    total_price = undiscounted_unit_price * checkout_line_info.line.quantity
    return quantize_price(total_price, total_price.currency)


def update_undiscounted_unit_price_for_lines(lines: Iterable["CheckoutLineInfo"]):
    """Update line undiscounted unit price amount.

    Undiscounted unit price stores the denormalized price of the variant.
    """
    for line_info in lines:
        if not line_info.channel_listing or line_info.channel_listing.price is None:
            continue

        line_info.line.undiscounted_unit_price = line_info.undiscounted_unit_price


def update_prior_unit_price_for_lines(lines: Iterable["CheckoutLineInfo"]):
    """Update line prior unit price amount.

    Prior unit price stores the price of the variant before promotion.
    """
    for line_info in lines:
        listing = line_info.channel_listing
        if not listing:
            continue

        # Updating amount instead of Money to avoid overriding currency with None
        if listing.prior_price_amount is None:
            line_info.line.prior_unit_price_amount = None
        else:
            line_info.line.prior_unit_price_amount = line_info.prior_unit_price_amount


def _fetch_checkout_prices_if_expired(
    checkout_info: "CheckoutInfo",
    manager: "PluginsManager",
    lines: list["CheckoutLineInfo"],
    allow_sync_webhooks: bool,
    force_update: bool = False,
    database_connection_name: str = settings.DATABASE_CONNECTION_DEFAULT_NAME,
    pregenerated_subscription_payloads: dict | None = None,
) -> tuple["CheckoutInfo", list["CheckoutLineInfo"]]:
    """Fetch checkout prices with taxes.

    First calculate and apply all checkout prices with taxes separately,
    then apply tax data as well if we receive one.

    Prices can be updated only if force_update == True, or if time elapsed from the
    last price update is greater than settings.CHECKOUT_PRICES_TTL.
    """
    from .utils import checkout_info_for_logs

    if pregenerated_subscription_payloads is None:
        pregenerated_subscription_payloads = {}

    checkout = checkout_info.checkout

    if not force_update and checkout.price_expiration > timezone.now():
        return checkout_info, lines

    tax_configuration = checkout_info.tax_configuration
    tax_calculation_strategy = get_tax_calculation_strategy_for_checkout(
        checkout_info, database_connection_name=database_connection_name
    )

    if (
        tax_calculation_strategy == TaxCalculationStrategy.TAX_APP
        and not allow_sync_webhooks
    ):
        return checkout_info, lines

    prices_entered_with_tax = tax_configuration.prices_entered_with_tax
    charge_taxes = get_charge_taxes_for_checkout(
        checkout_info, database_connection_name=database_connection_name
    )
    should_charge_tax = charge_taxes and not checkout.tax_exemption
    tax_app_identifier = get_tax_app_identifier_for_checkout(
        checkout_info, database_connection_name
    )

    try:
        recalculate_discounts(
            checkout_info,
            lines,
            database_connection_name=database_connection_name,
            force_update=force_update,
        )
    except Checkout.DoesNotExist:
        # Checkout was removed or converted to a order. Return data without saving.
        return checkout_info, lines

    checkout.tax_error = None

    no_need_to_calculate_taxes = not prices_entered_with_tax and not should_charge_tax
    if no_need_to_calculate_taxes:
        # Calculate net prices without taxes.
        _set_checkout_base_prices(checkout, checkout_info, lines)
    else:
        try:
            _calculate_and_add_tax(
                tax_calculation_strategy,
                tax_app_identifier,
                checkout,
                manager,
                checkout_info,
                lines,
                prices_entered_with_tax,
                database_connection_name=database_connection_name,
                pregenerated_subscription_payloads=pregenerated_subscription_payloads,
            )
        except TaxDataError as e:
            if str(e) != TaxDataErrorMessage.EMPTY:
                extra = checkout_info_for_logs(checkout_info, lines)
                if e.errors:
                    extra["errors"] = e.errors
                logger.warning(str(e), extra=extra)
            _set_checkout_base_prices(checkout, checkout_info, lines)
            checkout.tax_error = str(e)

        if not should_charge_tax:
            # If charge_taxes is disabled or checkout is exempt from taxes, remove the
            # tax from the original gross prices.
            _remove_tax(checkout, lines)

    price_expiration = timezone.now() + settings.CHECKOUT_PRICES_TTL
    checkout.price_expiration = price_expiration
    checkout.discount_expiration = price_expiration

    with allow_writer():
        with transaction.atomic():
            try:
                locked_checkout = (
                    checkout_qs_select_for_update()
                    .only("last_change")
                    .get(token=checkout.token)
                )
            except Checkout.DoesNotExist:
                # Checkout was removed or converted to a order. Return data without saving.
                return checkout_info, lines

            # Check whether the checkout has been modified during the recalculation process by another process.
            # If so, we should skip saving. The same applies if the checkout has been removed. This is important
            # to avoid overwriting changes made by the other requests. Skipping the save function does not affect
            # the query response because it returns the adjusted checkout and line info objects.
            if checkout.last_change == locked_checkout.last_change:
                checkout_update_fields = [
                    "voucher_code",
                    "total_net_amount",
                    "total_gross_amount",
                    "subtotal_net_amount",
                    "subtotal_gross_amount",
                    "shipping_price_net_amount",
                    "shipping_price_gross_amount",
                    "undiscounted_base_shipping_price_amount",
                    "shipping_tax_rate",
                    "translated_discount_name",
                    "discount_amount",
                    "discount_name",
                    "currency",
                    "price_expiration",
                    "discount_expiration",
                    "tax_error",
                ]

                from .utils import checkout_lines_bulk_update

                checkout.save(
                    update_fields=checkout_update_fields,
                    using=settings.DATABASE_CONNECTION_DEFAULT_NAME,
                )
                checkout_lines_bulk_update(
                    [line_info.line for line_info in lines],
                    [
                        "total_price_net_amount",
                        "total_price_gross_amount",
                        "tax_rate",
                        "undiscounted_unit_price_amount",
                        "prior_unit_price_amount",
                    ],
                )
    return checkout_info, lines


@allow_writer()
def recalculate_discounts(
    checkout_info: "CheckoutInfo",
    lines_info: Iterable["CheckoutLineInfo"],
    database_connection_name: str = settings.DATABASE_CONNECTION_DEFAULT_NAME,
    force_update: bool = False,
) -> tuple["CheckoutInfo", Iterable["CheckoutLineInfo"]]:
    """Recalculate checkout discounts.

    Discounts are recalculated only if force_update is True, or if both discount
    and price expirations have passed.
    This updates catalogue promotions, vouchers, and order promotion discounts.
    """
    checkout = checkout_info.checkout

    # Do not recalculate discounts in case the checkout prices are still valid, either
    # discounts or tax prices.
    if not force_update and (
        checkout.discount_expiration > timezone.now()
        or checkout.price_expiration > timezone.now()
    ):
        return checkout_info, lines_info

    lines = cast(list, lines_info)
    update_undiscounted_unit_price_for_lines(lines)
    update_prior_unit_price_for_lines(lines)

    soonest_promotion_end_date = (
        create_or_update_discount_objects_from_promotion_for_checkout(
            checkout_info, lines, database_connection_name
        )
    )

    if soonest_promotion_end_date is not None:
        checkout.discount_expiration = min(
            soonest_promotion_end_date, timezone.now() + settings.CHECKOUT_PRICES_TTL
        )
    else:
        checkout.discount_expiration = timezone.now() + settings.CHECKOUT_PRICES_TTL

    checkout.safe_update(
        update_fields=["discount_expiration"],
    )

    return checkout_info, lines


def _calculate_and_add_tax(
    tax_calculation_strategy: str,
    tax_app_identifier: str | None,
    checkout: "Checkout",
    manager: "PluginsManager",
    checkout_info: "CheckoutInfo",
    lines: list["CheckoutLineInfo"],
    prices_entered_with_tax: bool,
    database_connection_name: str = settings.DATABASE_CONNECTION_DEFAULT_NAME,
    pregenerated_subscription_payloads: dict | None = None,
):
    if pregenerated_subscription_payloads is None:
        pregenerated_subscription_payloads = {}

    if tax_calculation_strategy != TaxCalculationStrategy.TAX_APP:
        # Get taxes calculated with flat rates and apply to checkout.
        update_checkout_prices_with_flat_rates(
            checkout,
            checkout_info,
            lines,
            prices_entered_with_tax,
            database_connection_name=database_connection_name,
        )
        return

    # If taxAppId is not configured run all active plugins and tax apps.
    # If taxAppId is provided run tax plugin or Tax App. taxAppId can be
    # configured with Avatax plugin identifier.
    if not tax_app_identifier:
        # Call the tax plugins.
        _apply_tax_data_from_plugins(checkout, manager, checkout_info, lines)
        # Get the taxes calculated with apps and apply to checkout.
        # We should allow empty tax_data in case any tax webhook has not been
        # configured - handled by `allowed_empty_tax_data`
        tax_data = _get_taxes_for_checkout(
            checkout_info,
            lines,
            tax_app_identifier,
            manager,
            pregenerated_subscription_payloads,
            allowed_empty_tax_data=True,
        )
        _apply_tax_data(checkout, lines, tax_data)
    else:
        _call_plugin_or_tax_app(
            tax_app_identifier,
            checkout,
            manager,
            checkout_info,
            lines,
            pregenerated_subscription_payloads,
        )


def _call_plugin_or_tax_app(
    tax_app_identifier: str,
    checkout: "Checkout",
    manager: "PluginsManager",
    checkout_info: "CheckoutInfo",
    lines: list["CheckoutLineInfo"],
    pregenerated_subscription_payloads: dict | None = None,
):
    if pregenerated_subscription_payloads is None:
        pregenerated_subscription_payloads = {}

    if tax_app_identifier.startswith(PLUGIN_IDENTIFIER_PREFIX):
        plugin_ids = [tax_app_identifier.replace(PLUGIN_IDENTIFIER_PREFIX, "")]
        plugins = manager.get_plugins(
            checkout_info.channel.slug,
            active_only=True,
            plugin_ids=plugin_ids,
        )
        if not plugins:
            raise TaxDataError(TaxDataErrorMessage.EMPTY)
        _apply_tax_data_from_plugins(
            checkout,
            manager,
            checkout_info,
            lines,
            plugin_ids=plugin_ids,
        )
        if checkout.tax_error:
            raise TaxDataError(checkout.tax_error)
    else:
        tax_data = _get_taxes_for_checkout(
            checkout_info,
            lines,
            tax_app_identifier,
            manager,
            pregenerated_subscription_payloads,
        )
        _apply_tax_data(checkout, lines, tax_data)


def _get_taxes_for_checkout(
    checkout_info: "CheckoutInfo",
    lines: list["CheckoutLineInfo"],
    tax_app_identifier: str | None,
    manager: "PluginsManager",
    pregenerated_subscription_payloads: dict | None = None,
    allowed_empty_tax_data: bool = False,
):
    """Get taxes for checkout from tax apps.

    The `allowed_empty_tax_data` flag prevents an error from being raised when tax data
    is missing due to the absence of a configured tax app.
    """
    from .utils import log_address_if_validation_skipped_for_checkout

    if pregenerated_subscription_payloads is None:
        pregenerated_subscription_payloads = {}
    tax_data = None
    try:
        tax_data = manager.get_taxes_for_checkout(
            checkout_info,
            lines,
            tax_app_identifier,
            pregenerated_subscription_payloads=pregenerated_subscription_payloads,
        )
    except TaxDataError as e:
        raise e from e
    finally:
        # log in case the tax_data is missing
        if tax_data is None:
            log_address_if_validation_skipped_for_checkout(checkout_info, logger)

    if not tax_data and not allowed_empty_tax_data:
        raise TaxDataError(TaxDataErrorMessage.EMPTY)

    return tax_data


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
    lines: list["CheckoutLineInfo"],
    tax_data: TaxData | None,
) -> None:
    if not tax_data:
        return

    currency = checkout.currency
    for line_info, tax_line_data in zip(lines, tax_data.lines, strict=False):
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
    lines: list["CheckoutLineInfo"],
    plugin_ids: list[str] | None = None,
) -> None:
    address = checkout_info.shipping_address or checkout_info.billing_address
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
    lines: list["CheckoutLineInfo"],
) -> None:
    currency = checkout_info.checkout.currency
    subtotal = zero_money(currency)

    for line_info in lines:
        line = line_info.line
        total_price = (
            base_calculations.get_line_total_price_with_propagated_checkout_discount(
                checkout_info, lines, line_info
            )
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
    lines: list["CheckoutLineInfo"],
    force_update: bool = False,
    checkout_transactions: Iterable["TransactionItem"] | None = None,
    force_status_update: bool = False,
    database_connection_name: str = settings.DATABASE_CONNECTION_DEFAULT_NAME,
    pregenerated_subscription_payloads: dict | None = None,
    allow_sync_webhooks: bool = True,
):
    """Fetch checkout data.

    This function refreshes prices if they have expired. If the checkout total has
    changed as a result, it will update the payment statuses accordingly.
    """
    if pregenerated_subscription_payloads is None:
        pregenerated_subscription_payloads = {}
    previous_checkout_price_expiration = checkout_info.checkout.price_expiration
    checkout_info, lines = _fetch_checkout_prices_if_expired(
        checkout_info=checkout_info,
        manager=manager,
        lines=lines,
        force_update=force_update,
        database_connection_name=database_connection_name,
        pregenerated_subscription_payloads=pregenerated_subscription_payloads,
        allow_sync_webhooks=allow_sync_webhooks,
    )
    current_total_gross = checkout_info.checkout.total.gross
    if (
        checkout_info.checkout.price_expiration != previous_checkout_price_expiration
        or force_status_update
        or (
            # Checkout with total being zero is fully authorized therefore
            # if authorized status was not yet updated, do it now.
            current_total_gross == zero_money(current_total_gross.currency)
            and checkout_info.checkout.authorize_status != CheckoutAuthorizeStatus.FULL
            and bool(lines)
        )
    ):
        current_total_gross = (
            checkout_info.checkout.total.gross
            - checkout_info.checkout.get_total_gift_cards_balance(
                database_connection_name
            )
        )
        current_total_gross = max(
            current_total_gross, zero_money(current_total_gross.currency)
        )
        update_checkout_payment_statuses(
            checkout=checkout_info.checkout,
            checkout_total_gross=current_total_gross,
            checkout_has_lines=bool(lines),
            checkout_transactions=checkout_transactions,
            database_connection_name=database_connection_name,
        )

    return checkout_info, lines
