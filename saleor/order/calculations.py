import logging
from collections.abc import Iterable
from decimal import Decimal
from typing import TYPE_CHECKING, Union
from uuid import UUID

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from prices import Money, TaxedMoney
from promise import Promise

from ..core.db.connection import (
    allow_writer,
    allow_writer_for_default_connection,
)
from ..core.prices import quantize_price
from ..core.taxes import (
    TaxData,
    TaxDataError,
    TaxDataErrorMessage,
    TaxError,
    zero_taxed_money,
)
from ..discount.utils.order import (
    handle_order_promotion,
    refresh_manual_line_discount_object,
    refresh_order_line_discount_objects_for_catalogue_promotions,
    update_unit_discount_data_on_order_lines_info,
)
from ..discount.utils.voucher import (
    create_or_update_line_discount_objects_from_voucher,
    get_the_cheapest_line,
)
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
from . import ORDER_EDITABLE_STATUS, OrderStatus
from .base_calculations import base_order_line_total, calculate_prices
from .fetch import (
    EditableOrderLineInfo,
    fetch_draft_order_lines_info,
    reattach_apply_once_per_order_voucher_info,
)
from .interface import OrderTaxedPricesData
from .lock_objects import order_qs_select_for_update
from .models import Order, OrderLine
from .utils import (
    calculate_draft_order_line_price_expiration_date,
    log_address_if_validation_skipped_for_order,
    order_info_for_logs,
)

if TYPE_CHECKING:
    from ..account.models import User
    from ..app.models import App

logger = logging.getLogger(__name__)


def should_refresh_prices(
    order: Order,
    force_update: bool,
    expired_line_ids: list[UUID],
    database_connection_name: str = settings.DATABASE_CONNECTION_DEFAULT_NAME,
    allow_sync_webhooks: bool = True,
) -> bool:
    if order.status not in ORDER_EDITABLE_STATUS:
        return False

    if not force_update and not order.should_refresh_prices and not expired_line_ids:
        return False

    with allow_writer_for_default_connection(database_connection_name):
        tax_strategy = get_tax_calculation_strategy_for_order(order)
        if tax_strategy == TaxCalculationStrategy.TAX_APP and not allow_sync_webhooks:
            return False
    return True


def prepare_order_lines_for_refresh(
    order: Order,
    lines: Iterable[OrderLine] | None,
    expired_line_ids: list[UUID],
    database_connection_name: str = settings.DATABASE_CONNECTION_DEFAULT_NAME,
) -> list[EditableOrderLineInfo] | None:
    with allow_writer_for_default_connection(database_connection_name):
        if expired_line_ids:
            # handle line base price expiration
            return refresh_order_base_prices_and_discounts(
                order, expired_line_ids, lines
            )

        return fetch_draft_order_lines_info(order, lines)


def process_order_promotion(
    order: Order,
    lines_info: list[EditableOrderLineInfo],
    database_connection_name: str = settings.DATABASE_CONNECTION_DEFAULT_NAME,
):
    with allow_writer_for_default_connection(database_connection_name):
        # order promotion is qualified based on the most actual prices, therefor need to be assessed
        # on the every recalculation
        handle_order_promotion(order, lines_info, database_connection_name)


def process_order_prices(
    order: Order,
    manager: PluginsManager,
    requestor: Union["App", "User", None],
    lines: list[OrderLine],
    database_connection_name: str = settings.DATABASE_CONNECTION_DEFAULT_NAME,
) -> Promise[tuple[Order, Iterable[OrderLine]]]:
    def process_calculation_result(_):
        order.should_refresh_prices = False
        with allow_writer():
            with transaction.atomic(savepoint=False):
                try:
                    locked_order = (
                        order_qs_select_for_update().only("updated_at").get(id=order.id)
                    )
                except Order.DoesNotExist:
                    # Order was removed. Return data without saving.
                    return order, lines

                # Check whether the order has been modified during the recalculation process by another process.
                # If so, we should skip saving. The same applies if the order has been removed. This is important
                # to avoid overwriting changes made by the other requests. Skipping the save function does not affect
                # the query response because it returns the adjusted order and line info objects.
                if locked_order.updated_at == order.updated_at:
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
                            "base_shipping_price_amount",
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
                        ],
                    )
            return order, lines

    with allow_writer_for_default_connection(database_connection_name):
        calculate_prices(
            order,
            lines,
            database_connection_name=database_connection_name,
        )

        tax_strategy = get_tax_calculation_strategy_for_order(order)

        return calculate_taxes(
            order,
            manager,
            lines,
            tax_calculation_strategy=tax_strategy,
            database_connection_name=database_connection_name,
            requestor=requestor,
        ).then(process_calculation_result)


def fetch_order_prices_if_expired(
    order: Order,
    manager: PluginsManager,
    requestor: Union["App", "User", None],
    lines: Iterable[OrderLine] | None = None,
    force_update: bool = False,
    database_connection_name: str = settings.DATABASE_CONNECTION_DEFAULT_NAME,
    allow_sync_webhooks: bool = True,
) -> Promise[tuple[Order, Iterable[OrderLine]]]:
    """Fetch order prices with taxes.

    First applies order level discounts, then calculates taxes.

    Prices will be updated if force_update is True
    or if order.should_refresh_prices is True.
    """

    expired_line_ids = get_expired_line_ids(order, lines)
    if not should_refresh_prices(
        order=order,
        force_update=force_update,
        expired_line_ids=expired_line_ids,
        database_connection_name=database_connection_name,
        allow_sync_webhooks=allow_sync_webhooks,
    ):
        return Promise.resolve((order, lines or []))

    lines_info = prepare_order_lines_for_refresh(
        order=order,
        lines=lines,
        expired_line_ids=expired_line_ids,
        database_connection_name=database_connection_name,
    )

    if lines_info is None:
        return Promise.resolve((order, lines or []))

    process_order_promotion(
        order, lines_info, database_connection_name=database_connection_name
    )

    return process_order_prices(
        order=order,
        manager=manager,
        requestor=requestor,
        lines=[line_info.line for line_info in lines_info],
        database_connection_name=database_connection_name,
    )


def get_expired_line_ids(order: Order, lines: Iterable[OrderLine] | None) -> list[UUID]:
    if order.status != OrderStatus.DRAFT:
        return []

    if lines is None:
        lines = order.lines.all()
    now = timezone.now()
    return [
        line.pk
        for line in lines
        if line.draft_base_price_expire_at and line.draft_base_price_expire_at < now
    ]


def promise_calculate_taxes_with_error_handling(
    tax_calculation_strategy: str,
    tax_app_identifier: str | None,
    order: Order,
    lines: Iterable[OrderLine],
    manager: PluginsManager,
    prices_entered_with_tax: bool,
    requestor: Union["App", "User", None],
    database_connection_name: str,
) -> Promise[None]:
    def process_error(e: Exception):
        if not isinstance(e, TaxDataError):
            raise e
        if str(e) != TaxDataErrorMessage.EMPTY:
            extra = order_info_for_logs(order, lines)
            if getattr(e, "errors", None):
                extra["errors"] = e.errors
            logger.warning(str(e), extra=extra)
        order.tax_error = str(e)

    return _calculate_and_add_tax(
        tax_calculation_strategy,
        tax_app_identifier,
        order,
        lines,
        manager,
        prices_entered_with_tax,
        requestor=requestor,
        database_connection_name=database_connection_name,
    ).catch(process_error)


def calculate_taxes(
    order: Order,
    manager: PluginsManager,
    lines: Iterable[OrderLine],
    tax_calculation_strategy: str,
    requestor: Union["App", "User", None],
    database_connection_name: str = settings.DATABASE_CONNECTION_DEFAULT_NAME,
) -> Promise[None]:
    tax_configuration = order.channel.tax_configuration
    prices_entered_with_tax = tax_configuration.prices_entered_with_tax
    charge_taxes = get_charge_taxes_for_order(order)
    should_charge_tax = charge_taxes and not order.tax_exemption
    tax_app_identifier = get_tax_app_identifier_for_order(order)

    order.tax_error = None

    def remove_tax_if_needed(_):
        if should_charge_tax:
            return
        # If charge_taxes is disabled or order is exempt from taxes, remove the
        # tax from the original gross prices.
        remove_tax(order, lines, prices_entered_with_tax)

    if prices_entered_with_tax:
        return promise_calculate_taxes_with_error_handling(
            tax_calculation_strategy=tax_calculation_strategy,
            tax_app_identifier=tax_app_identifier,
            order=order,
            lines=lines,
            manager=manager,
            prices_entered_with_tax=prices_entered_with_tax,
            requestor=requestor,
            database_connection_name=database_connection_name,
        ).then(remove_tax_if_needed, remove_tax_if_needed)

    # Prices are entered without taxes.
    if not should_charge_tax:
        return Promise.resolve(None).then(remove_tax_if_needed)

    return promise_calculate_taxes_with_error_handling(
        tax_calculation_strategy=tax_calculation_strategy,
        tax_app_identifier=tax_app_identifier,
        order=order,
        lines=lines,
        manager=manager,
        prices_entered_with_tax=prices_entered_with_tax,
        requestor=requestor,
        database_connection_name=database_connection_name,
    )


def _calculate_and_add_tax(
    tax_calculation_strategy: str,
    tax_app_identifier: str | None,
    order: "Order",
    lines: Iterable["OrderLine"],
    manager: "PluginsManager",
    prices_entered_with_tax: bool,
    requestor: Union["App", "User", None],
    database_connection_name: str = settings.DATABASE_CONNECTION_DEFAULT_NAME,
) -> Promise[None]:
    @allow_writer_for_default_connection(database_connection_name)
    def process_flat_taxes(_):
        # Get taxes calculated with flat rates and apply to order.
        update_order_prices_with_flat_rates(
            order,
            lines,
            prices_entered_with_tax,
            database_connection_name=database_connection_name,
        )

    if tax_calculation_strategy == TaxCalculationStrategy.FLAT_RATES:
        return Promise.resolve(None).then(process_flat_taxes)

    if tax_app_identifier:
        return _call_plugin_or_tax_app(
            tax_app_identifier,
            order,
            lines,
            manager,
            prices_entered_with_tax,
            requestor=requestor,
        )

    # Deprecated flow when no tax app identifier is provided.
    def recalculate_with_tax_app_data(tax_data: TaxData | None):
        _apply_tax_data(order, lines, tax_data, prices_entered_with_tax)

    _recalculate_with_plugins(manager, order, lines, prices_entered_with_tax)
    # Get the taxes calculated with apps and apply to order.
    # We should allow empty tax_data in case any tax webhook has not been
    # configured - handled by `allowed_empty_tax_data`
    return _get_promised_taxes_for_order(
        order,
        lines=lines,
        tax_app_identifier=None,
        allowed_empty_tax_data=True,
        requestor=requestor,
    ).then(recalculate_with_tax_app_data)


def _call_plugin_or_tax_app(
    tax_app_identifier: str,
    order: "Order",
    lines: Iterable["OrderLine"],
    manager: "PluginsManager",
    prices_entered_with_tax: bool,
    requestor: Union["App", "User", None],
) -> Promise[None]:
    def recalculate_with_plugins(_):
        plugin_ids = [tax_app_identifier.replace(PLUGIN_IDENTIFIER_PREFIX, "")]
        plugins = manager.get_plugins(
            order.channel.slug, active_only=True, plugin_ids=plugin_ids
        )
        if not plugins:
            return Promise.reject(TaxDataError(TaxDataErrorMessage.EMPTY))
        _recalculate_with_plugins(
            manager,
            order,
            lines,
            prices_entered_with_tax,
            plugin_ids=plugin_ids,
        )
        if order.tax_error:
            return Promise.reject(TaxDataError(order.tax_error))
        return Promise.resolve(None)

    def recalculate_with_tax_app_data(tax_data: TaxData | None):
        _apply_tax_data(order, lines, tax_data, prices_entered_with_tax)

    if tax_app_identifier.startswith(PLUGIN_IDENTIFIER_PREFIX):
        return Promise.resolve(None).then(recalculate_with_plugins)

    return _get_promised_taxes_for_order(
        order, lines, tax_app_identifier, requestor=requestor
    ).then(recalculate_with_tax_app_data)


def _get_promised_taxes_for_order(
    order: "Order",
    lines: Iterable["OrderLine"],
    tax_app_identifier: str | None,
    requestor: Union["App", "User", None],
    allowed_empty_tax_data: bool = False,
) -> Promise[TaxData | None]:
    """Get taxes for order from tax apps.

    The `allowed_empty_tax_data` flag prevents an error from being raised when tax data
    is missing due to the absence of a configured tax app.
    """
    from .webhooks import order_calculate_taxes

    def process_error(e: Exception):
        if isinstance(e, TaxDataError):
            log_address_if_validation_skipped_for_order(order, logger)
        return Promise.reject(e)

    def process_response(tax_data: TaxData | None) -> Promise[TaxData | None]:
        if tax_data is None:
            log_address_if_validation_skipped_for_order(order, logger)

        if not tax_data and not allowed_empty_tax_data:
            return Promise.reject(TaxDataError(TaxDataErrorMessage.EMPTY))
        return Promise.resolve(tax_data)

    return (
        order_calculate_taxes.get_taxes(order, lines, tax_app_identifier, requestor)
        .then(process_response)
        .catch(process_error)
    )


def _recalculate_with_plugins(
    manager: PluginsManager,
    order: Order,
    lines: Iterable[OrderLine],
    prices_entered_with_tax: bool,
    plugin_ids: list[str] | None = None,
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
                line,
                product,
                variant,
                None,
                line.total_price,
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

    undiscounted_shipping_price = order.undiscounted_base_shipping_price
    order.undiscounted_total = undiscounted_subtotal + TaxedMoney(
        net=undiscounted_shipping_price, gross=undiscounted_shipping_price
    )
    order.subtotal = get_subtotal(lines, order.currency)
    order.total = manager.calculate_order_total(order, lines, plugin_ids=plugin_ids)


def _get_undiscounted_price(
    line_price: OrderTaxedPricesData,
    undiscounted_base_price: Money,
    tax_rate,
    prices_entered_with_tax,
) -> TaxedMoney:
    if (
        tax_rate > 0
        and line_price.undiscounted_price.net == line_price.undiscounted_price.gross
    ):
        return get_taxed_undiscounted_price(
            undiscounted_base_price,
            line_price.price_with_discounts,
            tax_rate,
            prices_entered_with_tax,
        )
    return line_price.undiscounted_price


def _apply_tax_data(
    order: Order,
    lines: Iterable[OrderLine],
    tax_data: TaxData | None,
    prices_entered_with_tax: bool,
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
    shipping_tax_rate = normalize_tax_rate_for_db(tax_data.shipping_tax_rate)
    order.shipping_tax_rate = shipping_tax_rate

    undiscounted_shipping_price = get_taxed_undiscounted_price(
        order.undiscounted_base_shipping_price,
        shipping_price,
        shipping_tax_rate,
        prices_entered_with_tax,
    )

    subtotal = zero_taxed_money(order.currency)
    undiscounted_subtotal = zero_taxed_money(order.currency)
    for order_line, tax_line in zip(lines, tax_data.lines, strict=False):
        line_total_price = TaxedMoney(
            net=Money(tax_line.total_net_amount, currency),
            gross=Money(tax_line.total_gross_amount, currency),
        )
        order_line.total_price = line_total_price
        order_line.unit_price = quantize_price(
            line_total_price / order_line.quantity, currency
        )
        line_tax_rate = normalize_tax_rate_for_db(tax_line.tax_rate)
        order_line.tax_rate = line_tax_rate
        subtotal += line_total_price

        order_line.undiscounted_unit_price = get_taxed_undiscounted_price(
            order_line.undiscounted_base_unit_price,
            order_line.unit_price,
            line_tax_rate,
            prices_entered_with_tax,
        )
        order_line.undiscounted_total_price = get_taxed_undiscounted_price(
            # base_order_line_total returns equal gross and net
            base_order_line_total(order_line).undiscounted_price.net,
            line_total_price,
            line_tax_rate,
            prices_entered_with_tax,
        )
        undiscounted_subtotal += order_line.undiscounted_total_price

    order.subtotal = subtotal
    order.total = shipping_price + subtotal
    order.undiscounted_total = undiscounted_shipping_price + undiscounted_subtotal


def remove_tax(order, lines, prices_entered_with_taxes):
    if prices_entered_with_taxes:
        _remove_tax_net(order, lines)
    else:
        _remove_tax_gross(order, lines)


def _remove_tax_gross(order, lines):
    """Set gross values equal to net values."""
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


def _remove_tax_net(order, lines):
    """Set net values equal to gross values."""
    order.total_net_amount = order.total_gross_amount
    order.undiscounted_total_net_amount = order.undiscounted_total_gross_amount
    order.subtotal_net_amount = order.subtotal_gross_amount
    order.shipping_price_net_amount = order.shipping_price_gross_amount
    order.shipping_tax_rate = Decimal("0.00")

    for line in lines:
        total_price_gross_amount = line.total_price_gross_amount
        unit_price_gross_amount = line.unit_price_gross_amount
        undiscounted_unit_price_gross_amount = line.undiscounted_unit_price_gross_amount
        undiscounted_total_price_gross_amount = (
            line.undiscounted_total_price_gross_amount
        )
        line.unit_price_net_amount = unit_price_gross_amount
        line.undiscounted_unit_price_net_amount = undiscounted_unit_price_gross_amount
        line.total_price_net_amount = total_price_gross_amount
        line.undiscounted_total_price_net_amount = undiscounted_total_price_gross_amount
        line.tax_rate = Decimal("0.00")


def _find_order_line(
    lines: Iterable[OrderLine] | None,
    order_line: OrderLine,
) -> OrderLine:
    """Return order line from provided lines.

    The return value represents the updated version of order_line parameter.
    """
    return next(
        (line for line in (lines or []) if line.pk == order_line.pk), order_line
    )


def refresh_order_base_prices_and_discounts(
    order: "Order",
    line_ids_to_refresh: Iterable[UUID],
    lines: Iterable[OrderLine] | None = None,
) -> list[EditableOrderLineInfo]:
    """Force order to fetch the latest channel listing prices and update discounts."""
    if order.status != OrderStatus.DRAFT:
        return []

    lines_info = fetch_draft_order_lines_info(
        order, lines=lines, fetch_actual_prices=True
    )
    if not lines_info:
        return []

    lines_info_to_update = [
        line_info
        for line_info in lines_info
        if line_info.line.id in line_ids_to_refresh
    ]

    initial_cheapest_line = get_the_cheapest_line(lines_info)

    # update prices based on the latest channel listing prices
    _set_channel_listing_prices(lines_info_to_update)
    # update prices based on the latest catalogue promotions
    refresh_order_line_discount_objects_for_catalogue_promotions(lines_info_to_update)
    # update manual line discount object amount based on the new listing prices
    refresh_manual_line_discount_object(lines_info_to_update)

    # update prices based on the associated voucher
    is_apply_once_per_order_voucher = (
        order.voucher and order.voucher.apply_once_per_order
    )
    if is_apply_once_per_order_voucher:
        # voucher of type apply once per order can impact other order line, if the
        # cheapest line has changed
        reattach_apply_once_per_order_voucher_info(
            lines_info, initial_cheapest_line, order
        )
        create_or_update_line_discount_objects_from_voucher(lines_info)
    else:
        create_or_update_line_discount_objects_from_voucher(lines_info_to_update)

    # update unit discount fields based on updated discounts
    update_unit_discount_data_on_order_lines_info(lines_info)

    # set price expiration time
    expiration_time = calculate_draft_order_line_price_expiration_date(
        order.channel, order.status
    )
    for line_info in lines_info_to_update:
        line_info.line.draft_base_price_expire_at = expiration_time

    lines = [line_info.line for line_info in lines_info]
    # cleanup after potential outdated prefetched line discounts
    _clear_prefetched_order_line_discounts(lines)
    OrderLine.objects.bulk_update(
        lines,
        [
            "unit_discount_amount",
            "unit_discount_reason",
            "unit_discount_type",
            "unit_discount_value",
            "base_unit_price_amount",
            "undiscounted_base_unit_price_amount",
            "draft_base_price_expire_at",
        ],
    )
    return lines_info


def _set_channel_listing_prices(lines_info: list[EditableOrderLineInfo]):
    for line_info in lines_info:
        line = line_info.line
        channel_listing = line_info.channel_listing
        if channel_listing and channel_listing.price_amount:
            line.undiscounted_base_unit_price_amount = channel_listing.price_amount
            line.base_unit_price_amount = channel_listing.price_amount


def _clear_prefetched_order_line_discounts(lines):
    for line in lines:
        if hasattr(line, "_prefetched_objects_cache"):
            line._prefetched_objects_cache.pop("discounts", None)


def refresh_all_order_base_prices_and_discounts(order):
    lines = order.lines.all()
    line_ids_to_refresh = [line.id for line in lines]
    refresh_order_base_prices_and_discounts(order, line_ids_to_refresh, lines)


def order_line_unit(
    order: Order,
    order_line: OrderLine,
    manager: PluginsManager,
    requestor: Union["App", "User", None],
    lines: Iterable[OrderLine] | None = None,
    force_update: bool = False,
    database_connection_name: str = settings.DATABASE_CONNECTION_DEFAULT_NAME,
    allow_sync_webhooks: bool = True,
) -> Promise[OrderTaxedPricesData]:
    """Return the unit price of provided line, taxes included.

    It takes into account all plugins.
    If the prices are expired, call all order price calculation methods
    and save them in the model directly.
    """
    currency = order.currency

    def process_result(result: tuple[Order, Iterable[OrderLine]]):
        _, lines = result
        line = _find_order_line(lines, order_line)
        return OrderTaxedPricesData(
            undiscounted_price=quantize_price(line.undiscounted_unit_price, currency),
            price_with_discounts=quantize_price(line.unit_price, currency),
        )

    return fetch_order_prices_if_expired(
        order,
        manager,
        requestor,
        lines,
        force_update,
        database_connection_name=database_connection_name,
        allow_sync_webhooks=allow_sync_webhooks,
    ).then(process_result)


def order_line_total(
    order: Order,
    order_line: OrderLine,
    manager: PluginsManager,
    requestor: Union["App", "User", None],
    lines: Iterable[OrderLine] | None = None,
    force_update: bool = False,
    database_connection_name: str = settings.DATABASE_CONNECTION_DEFAULT_NAME,
    allow_sync_webhooks: bool = True,
) -> Promise[OrderTaxedPricesData]:
    """Return the total price of provided line, taxes included.

    It takes into account all plugins.
    If the prices are expired, call all order price calculation methods
    and save them in the model directly.
    """
    currency = order.currency

    def process_result(result: tuple[Order, Iterable[OrderLine]]):
        _, lines = result
        line = _find_order_line(lines, order_line)
        return OrderTaxedPricesData(
            undiscounted_price=quantize_price(line.undiscounted_total_price, currency),
            price_with_discounts=quantize_price(line.total_price, currency),
        )

    return fetch_order_prices_if_expired(
        order,
        manager,
        requestor,
        lines,
        force_update,
        database_connection_name=database_connection_name,
        allow_sync_webhooks=allow_sync_webhooks,
    ).then(process_result)


def order_line_tax_rate(
    order: Order,
    order_line: OrderLine,
    manager: PluginsManager,
    requestor: Union["App", "User", None],
    lines: Iterable[OrderLine] | None = None,
    force_update: bool = False,
    database_connection_name: str = settings.DATABASE_CONNECTION_DEFAULT_NAME,
    allow_sync_webhooks: bool = True,
) -> Promise[Decimal | None]:
    """Return the tax rate of provided line.

    It takes into account all plugins.
    If the prices are expired, call all order price calculation methods
    and save them in the model directly.
    """

    def process_result(result: tuple[Order, Iterable[OrderLine]]):
        _, lines = result
        line = _find_order_line(lines, order_line)
        return line.tax_rate

    return fetch_order_prices_if_expired(
        order,
        manager,
        requestor,
        lines,
        force_update,
        database_connection_name=database_connection_name,
        allow_sync_webhooks=allow_sync_webhooks,
    ).then(process_result)


def order_line_unit_discount(
    order: Order,
    order_line: OrderLine,
    manager: PluginsManager,
    requestor: Union["App", "User", None],
    lines: Iterable[OrderLine] | None = None,
    force_update: bool = False,
    allow_sync_webhooks: bool = True,
) -> Promise[Decimal]:
    """Return the line unit discount.

    It takes into account all plugins.
    If the prices are expired, call all order price calculation methods
    and save them in the model directly.

    Line unit discount includes discounts from:
    - catalogue promotion
    - voucher applied on the line (`SPECIFIC_PRODUCT`, `apply_once_per_order` )
    - manual line discounts
    """

    def process_result(result: tuple[Order, Iterable[OrderLine]]):
        _, lines = result
        line = _find_order_line(lines, order_line)
        return line.unit_discount

    return fetch_order_prices_if_expired(
        order,
        manager,
        requestor,
        lines,
        force_update,
        allow_sync_webhooks=allow_sync_webhooks,
    ).then(process_result)


def order_line_unit_discount_value(
    order: Order,
    order_line: OrderLine,
    manager: PluginsManager,
    requestor: Union["App", "User", None],
    lines: Iterable[OrderLine] | None = None,
    force_update: bool = False,
    allow_sync_webhooks: bool = True,
) -> Promise[Decimal]:
    """Return the line unit discount value.

    It takes into account all plugins.
    If the prices are expired, call all order price calculation methods
    and save them in the model directly.
    """

    def process_result(result: tuple[Order, Iterable[OrderLine]]):
        _, lines = result
        line = _find_order_line(lines, order_line)
        return line.unit_discount_value

    return fetch_order_prices_if_expired(
        order,
        manager,
        requestor,
        lines,
        force_update,
        allow_sync_webhooks=allow_sync_webhooks,
    ).then(process_result)


def order_line_unit_discount_type(
    order: Order,
    order_line: OrderLine,
    manager: PluginsManager,
    requestor: Union["App", "User", None],
    lines: Iterable[OrderLine] | None = None,
    force_update: bool = False,
    allow_sync_webhooks: bool = True,
) -> Promise[str | None]:
    """Return the line unit discount type.

    It takes into account all plugins.
    If the prices are expired, call all order price calculation methods
    and save them in the model directly.
    """

    def process_result(result: tuple[Order, Iterable[OrderLine]]):
        _, lines = result
        line = _find_order_line(lines, order_line)
        return line.unit_discount_type

    return fetch_order_prices_if_expired(
        order,
        manager,
        requestor,
        lines,
        force_update,
        allow_sync_webhooks=allow_sync_webhooks,
    ).then(process_result)


def order_undiscounted_shipping(
    order: Order,
    manager: PluginsManager,
    requestor: Union["App", "User", None],
    lines: Iterable[OrderLine] | None = None,
    force_update: bool = False,
    database_connection_name: str = settings.DATABASE_CONNECTION_DEFAULT_NAME,
    allow_sync_webhooks: bool = True,
) -> Promise[TaxedMoney]:
    """Return the undiscounted shipping price of the order.

    It takes into account all plugins.
    If the prices are expired, call all order price calculation methods
    and save them in the model directly.
    """
    currency = order.currency

    def process_result(result: tuple[Order, Iterable[OrderLine]]):
        order, _ = result
        return quantize_price(order.undiscounted_base_shipping_price, currency)

    return fetch_order_prices_if_expired(
        order,
        manager,
        requestor,
        lines,
        force_update,
        database_connection_name=database_connection_name,
        allow_sync_webhooks=allow_sync_webhooks,
    ).then(process_result)


def order_shipping(
    order: Order,
    manager: PluginsManager,
    requestor: Union["App", "User", None],
    lines: Iterable[OrderLine] | None = None,
    force_update: bool = False,
    database_connection_name: str = settings.DATABASE_CONNECTION_DEFAULT_NAME,
    allow_sync_webhooks: bool = True,
) -> Promise[TaxedMoney]:
    """Return the shipping price of the order.

    It takes into account all plugins.
    If the prices are expired, call all order price calculation methods
    and save them in the model directly.
    """
    currency = order.currency

    def process_result(result: tuple[Order, Iterable[OrderLine]]):
        order, _ = result
        return quantize_price(order.shipping_price, currency)

    return fetch_order_prices_if_expired(
        order,
        manager,
        requestor,
        lines,
        force_update,
        database_connection_name=database_connection_name,
        allow_sync_webhooks=allow_sync_webhooks,
    ).then(process_result)


def order_shipping_tax_rate(
    order: Order,
    manager: PluginsManager,
    requestor: Union["App", "User", None],
    lines: Iterable[OrderLine] | None = None,
    force_update: bool = False,
    database_connection_name: str = settings.DATABASE_CONNECTION_DEFAULT_NAME,
    allow_sync_webhooks: bool = True,
) -> Promise[Decimal | None]:
    """Return the shipping tax rate of the order.

    It takes into account all plugins.
    If the prices are expired, call all order price calculation methods
    and save them in the model directly.
    """

    def process_result(result: tuple[Order, Iterable[OrderLine]]):
        order, _ = result
        return order.shipping_tax_rate

    return fetch_order_prices_if_expired(
        order,
        manager,
        requestor,
        lines,
        force_update,
        database_connection_name=database_connection_name,
        allow_sync_webhooks=allow_sync_webhooks,
    ).then(process_result)


def order_subtotal(
    order: Order,
    manager: PluginsManager,
    requestor: Union["App", "User", None],
    lines: Iterable[OrderLine] | None = None,
    force_update: bool = False,
    database_connection_name: str = settings.DATABASE_CONNECTION_DEFAULT_NAME,
    allow_sync_webhooks: bool = True,
) -> Promise[TaxedMoney]:
    """Return the total price of the order.

    It takes into account all plugins.
    If the prices are expired, call all order price calculation methods
    and save them in the model directly.
    """
    currency = order.currency

    def process_result(result: tuple[Order, Iterable[OrderLine]]):
        order, _ = result
        return quantize_price(order.subtotal, currency)

    return fetch_order_prices_if_expired(
        order,
        manager,
        requestor,
        lines,
        force_update,
        database_connection_name=database_connection_name,
        allow_sync_webhooks=allow_sync_webhooks,
    ).then(process_result)


def order_total(
    order: Order,
    manager: PluginsManager,
    requestor: Union["App", "User", None],
    lines: Iterable[OrderLine] | None = None,
    force_update: bool = False,
    database_connection_name: str = settings.DATABASE_CONNECTION_DEFAULT_NAME,
    allow_sync_webhooks: bool = True,
) -> Promise[TaxedMoney]:
    """Return the total price of the order.

    It takes into account all plugins.
    If the prices are expired, call all order price calculation methods
    and save them in the model directly.
    """
    currency = order.currency

    def process_result(result: tuple[Order, Iterable[OrderLine]]):
        order, _ = result
        return quantize_price(order.total, currency)

    return fetch_order_prices_if_expired(
        order,
        manager,
        requestor,
        lines,
        force_update,
        database_connection_name=database_connection_name,
        allow_sync_webhooks=allow_sync_webhooks,
    ).then(process_result)


def order_undiscounted_total(
    order: Order,
    manager: PluginsManager,
    requestor: Union["App", "User", None],
    lines: Iterable[OrderLine] | None = None,
    force_update: bool = False,
    database_connection_name: str = settings.DATABASE_CONNECTION_DEFAULT_NAME,
    allow_sync_webhooks: bool = True,
) -> Promise[TaxedMoney]:
    """Return the undiscounted total price of the order.

    It takes into account all plugins.
    If the prices are expired, call all order price calculation methods
    and save them in the model directly.
    """
    currency = order.currency

    def process_result(result: tuple[Order, Iterable[OrderLine]]):
        order, _ = result
        return quantize_price(order.undiscounted_total, currency)

    return fetch_order_prices_if_expired(
        order,
        manager,
        requestor,
        lines,
        force_update,
        database_connection_name=database_connection_name,
        allow_sync_webhooks=allow_sync_webhooks,
    ).then(process_result)
