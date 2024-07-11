import logging
from collections.abc import Iterable
from decimal import Decimal
from typing import Optional

from django.conf import settings
from django.db import transaction
from django.db.models import prefetch_related_objects
from prices import Money, TaxedMoney

from ..core.db.connection import allow_writer
from ..core.prices import quantize_price
from ..core.taxes import TaxData, TaxEmptyData, TaxError, zero_taxed_money
from ..discount import DiscountType
from ..discount.utils.order import create_or_update_discount_objects_for_order
from ..payment.model_helpers import get_subtotal
from ..plugins import PLUGIN_IDENTIFIER_PREFIX
from ..plugins.manager import PluginsManager
from ..tax import TaxCalculationStrategy
from ..tax.calculations import get_taxed_undiscounted_price
from ..tax.calculations.order import update_order_prices_with_flat_rates
from ..tax.utils import (
    get_charge_taxes_for_order,
    get_tax_app_identifier_for_order,
    get_tax_calculation_strategy_for_order,
    normalize_tax_rate_for_db,
)
from . import ORDER_EDITABLE_STATUS
from .base_calculations import apply_order_discounts, base_order_line_total
from .fetch import EditableOrderLineInfo, fetch_draft_order_lines_info
from .interface import OrderTaxedPricesData
from .models import Order, OrderLine
from .utils import log_address_if_validation_skipped_for_order

logger = logging.getLogger(__name__)


def fetch_order_prices_if_expired(
    order: Order,
    manager: PluginsManager,
    lines: Optional[Iterable[OrderLine]] = None,
    force_update: bool = False,
    database_connection_name: str = settings.DATABASE_CONNECTION_DEFAULT_NAME,
) -> tuple[Order, Optional[Iterable[OrderLine]]]:
    """Fetch order prices with taxes.

    First applies order level discounts, then calculates taxes.

    Prices will be updated if force_update is True
    or if order.should_refresh_prices is True.
    """
    if order.status not in ORDER_EDITABLE_STATUS:
        return order, lines

    if not force_update and not order.should_refresh_prices:
        return order, lines

    # handle promotions
    lines_info: list[EditableOrderLineInfo] = fetch_draft_order_lines_info(order, lines)
    create_or_update_discount_objects_for_order(
        order, lines_info, database_connection_name
    )
    lines = [line_info.line for line_info in lines_info]
    _update_order_discount_for_voucher(order)

    _clear_prefetched_discounts(order, lines)
    with allow_writer():
        # TODO: Load discounts with a dataloader and pass as argument
        prefetch_related_objects([order], "discounts")

    # handle taxes
    _recalculate_prices(
        order,
        manager,
        lines,
        database_connection_name=database_connection_name,
    )

    order.should_refresh_prices = False
    with transaction.atomic(savepoint=False):
        with allow_writer():
            order.save(
                update_fields=[
                    "subtotal_net_amount",
                    "subtotal_gross_amount",
                    "total_net_amount",
                    "total_gross_amount",
                    "undiscounted_total_net_amount",
                    "undiscounted_total_gross_amount",
                    "shipping_price_net_amount",
                    "shipping_price_gross_amount",
                    "shipping_tax_rate",
                    "should_refresh_prices",
                    "tax_error",
                ]
            )
            order.lines.bulk_update(
                lines,
                [
                    "unit_price_net_amount",
                    "unit_price_gross_amount",
                    "undiscounted_unit_price_net_amount",
                    "undiscounted_unit_price_gross_amount",
                    "total_price_net_amount",
                    "total_price_gross_amount",
                    "undiscounted_total_price_net_amount",
                    "undiscounted_total_price_gross_amount",
                    "tax_rate",
                    "unit_discount_amount",
                    "unit_discount_reason",
                    "unit_discount_type",
                    "unit_discount_value",
                    "base_unit_price_amount",
                ],
            )

        return order, lines


@allow_writer()
def _update_order_discount_for_voucher(order: Order):
    """Create or delete OrderDiscount instances."""
    if not order.voucher_id:
        order.discounts.filter(type=DiscountType.VOUCHER).delete()

    elif (
        order.voucher_id
        and not order.discounts.filter(voucher_code=order.voucher_code).exists()
    ):
        voucher = order.voucher
        voucher_channel_listing = voucher.channel_listings.filter(  # type: ignore
            channel=order.channel
        ).first()
        if voucher_channel_listing:
            order.discounts.create(
                value_type=voucher.discount_value_type,  # type: ignore
                value=voucher_channel_listing.discount_value,
                reason=f"Voucher: {voucher.name}",  # type: ignore
                voucher=voucher,
                type=DiscountType.VOUCHER,
                voucher_code=order.voucher_code,
            )


def _clear_prefetched_discounts(order, lines):
    if hasattr(order, "_prefetched_objects_cache"):
        order._prefetched_objects_cache.pop("discounts", None)

    for line in lines:
        if hasattr(line, "_prefetched_objects_cache"):
            line._prefetched_objects_cache.pop("discounts", None)


def _recalculate_prices(
    order: Order,
    manager: PluginsManager,
    lines: Iterable[OrderLine],
    database_connection_name: str = settings.DATABASE_CONNECTION_DEFAULT_NAME,
):
    """Calculate prices after handling order level discounts and taxes."""
    tax_configuration = order.channel.tax_configuration
    tax_calculation_strategy = get_tax_calculation_strategy_for_order(order)
    prices_entered_with_tax = tax_configuration.prices_entered_with_tax
    charge_taxes = get_charge_taxes_for_order(order)
    should_charge_tax = charge_taxes and not order.tax_exemption
    tax_app_identifier = get_tax_app_identifier_for_order(order)

    order.tax_error = None

    # propagate the order level discount on the prices without taxes.
    apply_order_discounts(
        order,
        lines,
        assign_prices=True,
        database_connection_name=database_connection_name,
    )
    if prices_entered_with_tax:
        # If prices are entered with tax, we need to always calculate it anyway, to
        # display the tax rate to the user.
        try:
            _calculate_and_add_tax(
                tax_calculation_strategy,
                tax_app_identifier,
                order,
                lines,
                manager,
                prices_entered_with_tax,
                database_connection_name=database_connection_name,
            )
        except TaxEmptyData as e:
            order.tax_error = str(e)

        if not should_charge_tax:
            # If charge_taxes is disabled or order is exempt from taxes, remove the
            # tax from the original gross prices.
            _remove_tax(order, lines)

    else:
        # Prices are entered without taxes.
        if should_charge_tax:
            # Calculate taxes if charge_taxes is enabled and order is not exempt
            # from taxes.
            try:
                _calculate_and_add_tax(
                    tax_calculation_strategy,
                    tax_app_identifier,
                    order,
                    lines,
                    manager,
                    prices_entered_with_tax,
                    database_connection_name=database_connection_name,
                )
            except TaxEmptyData as e:
                order.tax_error = str(e)
        else:
            _remove_tax(order, lines)


def _calculate_and_add_tax(
    tax_calculation_strategy: str,
    tax_app_identifier: Optional[str],
    order: "Order",
    lines: Iterable["OrderLine"],
    manager: "PluginsManager",
    prices_entered_with_tax: bool,
    database_connection_name: str = settings.DATABASE_CONNECTION_DEFAULT_NAME,
):
    if tax_calculation_strategy == TaxCalculationStrategy.TAX_APP:
        # If taxAppId is not configured run all active plugins and tax apps.
        # If taxAppId is provided run tax plugin or Tax App. taxAppId can be
        # configured with Avatax plugin identifier.
        if not tax_app_identifier:
            # Get the taxes calculated with plugins.
            _recalculate_with_plugins(manager, order, lines, prices_entered_with_tax)
            # Get the taxes calculated with apps and apply to order.
            tax_data = manager.get_taxes_for_order(order, tax_app_identifier)
            if not tax_data:
                log_address_if_validation_skipped_for_order(order, logger)
            _apply_tax_data(order, lines, tax_data)
        else:
            _call_plugin_or_tax_app(
                tax_app_identifier,
                order,
                lines,
                manager,
                prices_entered_with_tax,
            )
    else:
        # Get taxes calculated with flat rates and apply to order.
        update_order_prices_with_flat_rates(
            order,
            lines,
            prices_entered_with_tax,
            database_connection_name=database_connection_name,
        )


def _call_plugin_or_tax_app(
    tax_app_identifier: str,
    order: "Order",
    lines: Iterable["OrderLine"],
    manager: "PluginsManager",
    prices_entered_with_tax: bool,
):
    if tax_app_identifier.startswith(PLUGIN_IDENTIFIER_PREFIX):
        plugin_ids = [tax_app_identifier.replace(PLUGIN_IDENTIFIER_PREFIX, "")]
        plugins = manager.get_plugins(
            order.channel.slug, active_only=True, plugin_ids=plugin_ids
        )
        if not plugins:
            raise TaxEmptyData("Empty tax data.")
        _recalculate_with_plugins(
            manager,
            order,
            lines,
            prices_entered_with_tax,
            plugin_ids=plugin_ids,
        )
        if order.tax_error:
            raise TaxEmptyData("Empty tax data.")
    else:
        tax_data = manager.get_taxes_for_order(order, tax_app_identifier)
        if tax_data is None:
            log_address_if_validation_skipped_for_order(order, logger)
            raise TaxEmptyData("Empty tax data.")
        _apply_tax_data(order, lines, tax_data)


def _recalculate_with_plugins(
    manager: PluginsManager,
    order: Order,
    lines: Iterable[OrderLine],
    prices_entered_with_tax: bool,
    plugin_ids: Optional[list[str]] = None,
) -> None:
    """Fetch taxes from plugins and recalculate order/lines prices.

    Does not throw TaxError.
    """
    undiscounted_subtotal = zero_taxed_money(order.currency)
    for line in lines:
        variant = line.variant
        if not variant:
            continue
        product = variant.product

        try:
            line_unit = manager.calculate_order_line_unit(
                order, line, variant, product, lines, plugin_ids=plugin_ids
            )
            line.unit_price = line_unit.price_with_discounts

            line_total = manager.calculate_order_line_total(
                order, line, variant, product, lines, plugin_ids=plugin_ids
            )
            undiscounted_subtotal += line_total.undiscounted_price
            line.total_price = line_total.price_with_discounts

            line.tax_rate = manager.get_order_line_tax_rate(
                order,
                product,
                variant,
                None,
                line_unit.undiscounted_price,
                plugin_ids=plugin_ids,
            )
            line.undiscounted_unit_price = _get_undiscounted_price(
                line_unit,
                line.undiscounted_base_unit_price,
                line.tax_rate,
                prices_entered_with_tax,
            )

            line.undiscounted_total_price = _get_undiscounted_price(
                line_total,
                # base_order_line_total returns equal gross and net
                base_order_line_total(line).undiscounted_price.net,
                line.tax_rate,
                prices_entered_with_tax,
            )
        except TaxError:
            pass

    try:
        order.shipping_price = manager.calculate_order_shipping(
            order, lines, plugin_ids=plugin_ids
        )
        order.shipping_tax_rate = manager.get_order_shipping_tax_rate(
            order, order.shipping_price, plugin_ids=plugin_ids
        )
    except TaxError:
        pass

    order.undiscounted_total = undiscounted_subtotal + TaxedMoney(
        net=order.base_shipping_price, gross=order.base_shipping_price
    )
    order.subtotal = get_subtotal(lines, order.currency)
    order.total = manager.calculate_order_total(order, lines, plugin_ids=plugin_ids)


def _get_undiscounted_price(
    line_price: OrderTaxedPricesData,
    line_base_price: Money,
    tax_rate,
    prices_entered_with_tax,
):
    if (
        tax_rate > 0
        and line_price.undiscounted_price.net == line_price.undiscounted_price.gross
    ):
        get_taxed_undiscounted_price(
            line_base_price,
            line_price.undiscounted_price,
            tax_rate,
            prices_entered_with_tax,
        )
    return line_price.undiscounted_price


def _apply_tax_data(
    order: Order, lines: Iterable[OrderLine], tax_data: Optional[TaxData]
) -> None:
    """Apply all prices from tax data to order and order lines."""
    if not tax_data:
        return

    currency = order.currency
    shipping_price = TaxedMoney(
        net=Money(tax_data.shipping_price_net_amount, currency),
        gross=Money(tax_data.shipping_price_gross_amount, currency),
    )

    order.shipping_price = shipping_price
    order.shipping_tax_rate = normalize_tax_rate_for_db(tax_data.shipping_tax_rate)

    subtotal = zero_taxed_money(order.currency)
    for order_line, tax_line in zip(lines, tax_data.lines):
        line_total_price = TaxedMoney(
            net=Money(tax_line.total_net_amount, currency),
            gross=Money(tax_line.total_gross_amount, currency),
        )
        order_line.total_price = line_total_price
        order_line.unit_price = line_total_price / order_line.quantity
        order_line.tax_rate = normalize_tax_rate_for_db(tax_line.tax_rate)
        subtotal += line_total_price

    order.subtotal = subtotal
    order.total = shipping_price + subtotal


def _remove_tax(order, lines):
    order.total_gross_amount = order.total_net_amount
    order.undiscounted_total_gross_amount = order.undiscounted_total_net_amount
    order.subtotal_gross_amount = order.subtotal_net_amount
    order.shipping_price_gross_amount = order.shipping_price_net_amount
    order.shipping_tax_rate = Decimal("0.00")

    for line in lines:
        total_price_net_amount = line.total_price_net_amount
        unit_price_net_amount = line.unit_price_net_amount
        undiscounted_unit_price_net_amount = line.undiscounted_unit_price_net_amount
        undiscounted_total_price_net_amount = line.undiscounted_total_price_net_amount
        line.unit_price_gross_amount = unit_price_net_amount
        line.undiscounted_unit_price_gross_amount = undiscounted_unit_price_net_amount
        line.total_price_gross_amount = total_price_net_amount
        line.undiscounted_total_price_gross_amount = undiscounted_total_price_net_amount
        line.tax_rate = Decimal("0.00")


def _find_order_line(
    lines: Optional[Iterable[OrderLine]],
    order_line: OrderLine,
) -> OrderLine:
    """Return order line from provided lines.

    The return value represents the updated version of order_line parameter.
    """
    return next(
        (line for line in (lines or []) if line.pk == order_line.pk), order_line
    )


def order_line_unit(
    order: Order,
    order_line: OrderLine,
    manager: PluginsManager,
    lines: Optional[Iterable[OrderLine]] = None,
    force_update: bool = False,
    database_connection_name: str = settings.DATABASE_CONNECTION_DEFAULT_NAME,
) -> OrderTaxedPricesData:
    """Return the unit price of provided line, taxes included.

    It takes into account all plugins.
    If the prices are expired, call all order price calculation methods
    and save them in the model directly.
    """
    currency = order.currency
    _, lines = fetch_order_prices_if_expired(
        order,
        manager,
        lines,
        force_update,
        database_connection_name=database_connection_name,
    )
    order_line = _find_order_line(lines, order_line)
    return OrderTaxedPricesData(
        undiscounted_price=quantize_price(order_line.undiscounted_unit_price, currency),
        price_with_discounts=quantize_price(order_line.unit_price, currency),
    )


def order_line_total(
    order: Order,
    order_line: OrderLine,
    manager: PluginsManager,
    lines: Optional[Iterable[OrderLine]] = None,
    force_update: bool = False,
    database_connection_name: str = settings.DATABASE_CONNECTION_DEFAULT_NAME,
) -> OrderTaxedPricesData:
    """Return the total price of provided line, taxes included.

    It takes into account all plugins.
    If the prices are expired, call all order price calculation methods
    and save them in the model directly.
    """
    currency = order.currency
    _, lines = fetch_order_prices_if_expired(
        order,
        manager,
        lines,
        force_update,
        database_connection_name=database_connection_name,
    )
    order_line = _find_order_line(lines, order_line)
    return OrderTaxedPricesData(
        undiscounted_price=quantize_price(
            order_line.undiscounted_total_price, currency
        ),
        price_with_discounts=quantize_price(order_line.total_price, currency),
    )


def order_line_tax_rate(
    order: Order,
    order_line: OrderLine,
    manager: PluginsManager,
    lines: Optional[Iterable[OrderLine]] = None,
    force_update: bool = False,
    database_connection_name: str = settings.DATABASE_CONNECTION_DEFAULT_NAME,
) -> Optional[Decimal]:
    """Return the tax rate of provided line.

    It takes into account all plugins.
    If the prices are expired, call all order price calculation methods
    and save them in the model directly.
    """
    _, lines = fetch_order_prices_if_expired(
        order,
        manager,
        lines,
        force_update,
        database_connection_name=database_connection_name,
    )
    order_line = _find_order_line(lines, order_line)
    return order_line.tax_rate


def order_line_unit_discount(
    order: Order,
    order_line: OrderLine,
    manager: PluginsManager,
    lines: Optional[Iterable[OrderLine]] = None,
    force_update: bool = False,
) -> Decimal:
    """Return the line unit discount.

    It takes into account all plugins.
    If the prices are expired, call all order price calculation methods
    and save them in the model directly.

    Line unit discount includes discounts from:
    - catalogue promotion
    - voucher applied on the line (`SPECIFIC_PRODUCT`, `apply_once_per_order` )
    - manual line discounts
    """
    _, lines = fetch_order_prices_if_expired(order, manager, lines, force_update)
    order_line = _find_order_line(lines, order_line)
    return order_line.unit_discount


def order_line_unit_discount_value(
    order: Order,
    order_line: OrderLine,
    manager: PluginsManager,
    lines: Optional[Iterable[OrderLine]] = None,
    force_update: bool = False,
) -> Decimal:
    """Return the line unit discount value.

    It takes into account all plugins.
    If the prices are expired, call all order price calculation methods
    and save them in the model directly.
    """
    _, lines = fetch_order_prices_if_expired(order, manager, lines, force_update)
    order_line = _find_order_line(lines, order_line)
    return order_line.unit_discount_value


def order_line_unit_discount_type(
    order: Order,
    order_line: OrderLine,
    manager: PluginsManager,
    lines: Optional[Iterable[OrderLine]] = None,
    force_update: bool = False,
) -> Optional[str]:
    """Return the line unit discount type.

    It takes into account all plugins.
    If the prices are expired, call all order price calculation methods
    and save them in the model directly.
    """
    _, lines = fetch_order_prices_if_expired(order, manager, lines, force_update)
    order_line = _find_order_line(lines, order_line)
    return order_line.unit_discount_type


def order_shipping(
    order: Order,
    manager: PluginsManager,
    lines: Optional[Iterable[OrderLine]] = None,
    force_update: bool = False,
    database_connection_name: str = settings.DATABASE_CONNECTION_DEFAULT_NAME,
) -> TaxedMoney:
    """Return the shipping price of the order.

    It takes into account all plugins.
    If the prices are expired, call all order price calculation methods
    and save them in the model directly.
    """
    currency = order.currency
    order, _ = fetch_order_prices_if_expired(
        order,
        manager,
        lines,
        force_update,
        database_connection_name=database_connection_name,
    )
    return quantize_price(order.shipping_price, currency)


def order_shipping_tax_rate(
    order: Order,
    manager: PluginsManager,
    lines: Optional[Iterable[OrderLine]] = None,
    force_update: bool = False,
    database_connection_name: str = settings.DATABASE_CONNECTION_DEFAULT_NAME,
) -> Optional[Decimal]:
    """Return the shipping tax rate of the order.

    It takes into account all plugins.
    If the prices are expired, call all order price calculation methods
    and save them in the model directly.
    """
    order, _ = fetch_order_prices_if_expired(
        order,
        manager,
        lines,
        force_update,
        database_connection_name=database_connection_name,
    )
    return order.shipping_tax_rate


def order_subtotal(
    order: Order,
    manager: PluginsManager,
    lines: Optional[Iterable[OrderLine]] = None,
    force_update: bool = False,
    database_connection_name: str = settings.DATABASE_CONNECTION_DEFAULT_NAME,
):
    """Return the total price of the order.

    It takes into account all plugins.
    If the prices are expired, call all order price calculation methods
    and save them in the model directly.
    """
    currency = order.currency
    order, lines = fetch_order_prices_if_expired(
        order,
        manager,
        lines,
        force_update,
        database_connection_name=database_connection_name,
    )
    # Lines aren't returned only if
    # we don't pass them to `fetch_order_prices_if_expired`.
    return quantize_price(order.subtotal, currency)


def order_total(
    order: Order,
    manager: PluginsManager,
    lines: Optional[Iterable[OrderLine]] = None,
    force_update: bool = False,
    database_connection_name: str = settings.DATABASE_CONNECTION_DEFAULT_NAME,
) -> TaxedMoney:
    """Return the total price of the order.

    It takes into account all plugins.
    If the prices are expired, call all order price calculation methods
    and save them in the model directly.
    """
    currency = order.currency
    order, _ = fetch_order_prices_if_expired(
        order,
        manager,
        lines,
        force_update,
        database_connection_name=database_connection_name,
    )
    return quantize_price(order.total, currency)


def order_undiscounted_total(
    order: Order,
    manager: PluginsManager,
    lines: Optional[Iterable[OrderLine]] = None,
    force_update: bool = False,
    database_connection_name: str = settings.DATABASE_CONNECTION_DEFAULT_NAME,
) -> TaxedMoney:
    """Return the undiscounted total price of the order.

    It takes into account all plugins.
    If the prices are expired, call all order price calculation methods
    and save them in the model directly.
    """
    currency = order.currency
    order, _ = fetch_order_prices_if_expired(
        order,
        manager,
        lines,
        force_update,
        database_connection_name=database_connection_name,
    )
    return quantize_price(order.undiscounted_total, currency)
