from collections.abc import Iterable
from decimal import Decimal

from django.db import transaction
from django.db.models import prefetch_related_objects
from prices import Money, TaxedMoney

from ..core.prices import quantize_price
from ..core.taxes import TaxData, TaxError, zero_taxed_money
from ..discount import DiscountType
from ..payment.model_helpers import get_subtotal
from ..plugins.manager import PluginsManager
from ..tax import TaxCalculationStrategy
from ..tax.calculations import get_taxed_undiscounted_price
from ..tax.calculations.order import update_order_prices_with_flat_rates
from ..tax.utils import (
    get_charge_taxes_for_order,
    get_tax_calculation_strategy_for_order,
    normalize_tax_rate_for_db,
)
from . import ORDER_EDITABLE_STATUS
from .base_calculations import (
    apply_order_discounts,
    base_order_line_total,
    undiscounted_order_total,
    update_order_discount_amounts,
)
from .interface import OrderTaxedPricesData
from .models import Order, OrderLine


def fetch_order_prices_if_expired(
    order: Order,
    manager: PluginsManager,
    lines: Iterable[OrderLine] | None = None,
    force_update: bool = False,
) -> tuple[Order, Iterable[OrderLine] | None]:
    """Fetch order prices with taxes.

    First applies order level discounts, then calculates taxes.

    Prices will be updated if force_update is True
    or if order.should_refresh_prices is True.
    """
    if order.status not in ORDER_EDITABLE_STATUS:
        return order, lines

    if not force_update and not order.should_refresh_prices:
        return order, lines

    if lines is None:
        lines = list(order.lines.select_related("variant__product__product_type"))
    else:
        prefetch_related_objects(lines, "variant__product__product_type")

    order.should_refresh_prices = False

    _update_order_discount_for_voucher(order)
    _recalculate_prices(order, manager, lines)

    order.subtotal = get_subtotal(lines, order.currency)
    with transaction.atomic(savepoint=False):
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

    # Prefetch has to be cleared and refreshed to avoid returning cached discounts
    if (
        hasattr(order, "_prefetched_objects_cache")
        and "discounts" in order._prefetched_objects_cache
    ):
        del order._prefetched_objects_cache["discounts"]

    prefetch_related_objects([order], "discounts")


def _recalculate_prices(
    order: Order,
    manager: PluginsManager,
    lines: Iterable[OrderLine],
):
    """Calculate prices after handling order level discounts and taxes."""
    tax_configuration = order.channel.tax_configuration
    tax_calculation_strategy = get_tax_calculation_strategy_for_order(order)
    prices_entered_with_tax = tax_configuration.prices_entered_with_tax
    charge_taxes = get_charge_taxes_for_order(order)
    should_charge_tax = charge_taxes and not order.tax_exemption
    if prices_entered_with_tax:
        # If prices are entered with tax, we need to always calculate it anyway, to
        # display the tax rate to the user.
        _calculate_and_add_tax(
            tax_calculation_strategy, order, lines, manager, prices_entered_with_tax
        )
        if not should_charge_tax:
            # If charge_taxes is disabled or order is exempt from taxes, remove the
            # tax from the original gross prices.
            _remove_tax(order, lines)

    else:
        # Prices are entered without taxes.
        if should_charge_tax:
            # Calculate taxes if charge_taxes is enabled and order is not exempt
            # from taxes.
            _calculate_and_add_tax(
                tax_calculation_strategy, order, lines, manager, prices_entered_with_tax
            )
        else:
            apply_order_discounts(order, lines, assign_prices=True)
            _remove_tax(order, lines)


def _calculate_and_add_tax(
    tax_calculation_strategy: str,
    order: "Order",
    lines: Iterable["OrderLine"],
    manager: "PluginsManager",
    prices_entered_with_tax: bool,
):
    if tax_calculation_strategy == TaxCalculationStrategy.TAX_APP:
        # Get the taxes calculated with plugins.
        _recalculate_with_plugins(manager, order, lines, prices_entered_with_tax)
        # Get the taxes calculated with apps and apply to order.
        tax_data = manager.get_taxes_for_order(order)
        _apply_tax_data(order, lines, tax_data)
        # TODO: If tax data is empty, order level discounts are not propagated
        #  to its lines and not reflected in line total prices.
        #  https://github.com/saleor/saleor/issues/14880
    else:
        # Get taxes calculated with flat rates and apply to order.
        update_order_prices_with_flat_rates(order, lines, prices_entered_with_tax)


def _recalculate_with_plugins(
    manager: PluginsManager,
    order: Order,
    lines: Iterable[OrderLine],
    prices_entered_with_tax: bool,
) -> None:
    """Fetch taxes from plugins and recalculate order/lines prices.

    Does not throw TaxError.
    """
    _update_order_discounts_and_base_undiscounted_total(order, lines)
    undiscounted_subtotal = zero_taxed_money(order.currency)
    for line in lines:
        variant = line.variant
        if not variant:
            continue
        product = variant.product

        try:
            line_unit = manager.calculate_order_line_unit(order, line, variant, product)
            line.unit_price = line_unit.price_with_discounts

            line_total = manager.calculate_order_line_total(
                order, line, variant, product
            )
            undiscounted_subtotal += line_total.undiscounted_price
            line.total_price = line_total.price_with_discounts

            line.tax_rate = manager.get_order_line_tax_rate(
                order, product, variant, None, line_unit.undiscounted_price
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
        order.shipping_price = manager.calculate_order_shipping(order)
        order.shipping_tax_rate = manager.get_order_shipping_tax_rate(
            order, order.shipping_price
        )
    except TaxError:
        pass

    order.undiscounted_total = undiscounted_subtotal + TaxedMoney(
        net=order.base_shipping_price, gross=order.base_shipping_price
    )
    order.total = manager.calculate_order_total(order, lines)


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


def _update_order_discounts_and_base_undiscounted_total(
    order: Order, lines: Iterable[OrderLine]
):
    """Update order discounts and order undiscounted_total price.

    Entire order vouchers and staff order discounts are recalculated and updated.
    """
    update_order_discount_amounts(order, lines)
    undiscounted_total = undiscounted_order_total(order, lines)
    order.undiscounted_total = TaxedMoney(
        net=undiscounted_total, gross=undiscounted_total
    )


def _apply_tax_data(
    order: Order, lines: Iterable[OrderLine], tax_data: TaxData | None
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

    order.total = shipping_price + subtotal


def _remove_tax(order, lines):
    order.total_gross_amount = order.total_net_amount
    order.undiscounted_total_gross_amount = order.undiscounted_total_net_amount
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
    lines: Iterable[OrderLine] | None,
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
    lines: Iterable[OrderLine] | None = None,
    force_update: bool = False,
) -> OrderTaxedPricesData:
    """Return the unit price of provided line, taxes included.

    It takes into account all plugins.
    If the prices are expired, call all order price calculation methods
    and save them in the model directly.
    """
    currency = order.currency
    _, lines = fetch_order_prices_if_expired(order, manager, lines, force_update)
    order_line = _find_order_line(lines, order_line)
    return OrderTaxedPricesData(
        undiscounted_price=quantize_price(order_line.undiscounted_unit_price, currency),
        price_with_discounts=quantize_price(order_line.unit_price, currency),
    )


def order_line_total(
    order: Order,
    order_line: OrderLine,
    manager: PluginsManager,
    lines: Iterable[OrderLine] | None = None,
    force_update: bool = False,
) -> OrderTaxedPricesData:
    """Return the total price of provided line, taxes included.

    It takes into account all plugins.
    If the prices are expired, call all order price calculation methods
    and save them in the model directly.
    """
    currency = order.currency
    _, lines = fetch_order_prices_if_expired(order, manager, lines, force_update)
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
    lines: Iterable[OrderLine] | None = None,
    force_update: bool = False,
) -> Decimal | None:
    """Return the tax rate of provided line.

    It takes into account all plugins.
    If the prices are expired, call all order price calculation methods
    and save them in the model directly.
    """
    _, lines = fetch_order_prices_if_expired(order, manager, lines, force_update)
    order_line = _find_order_line(lines, order_line)
    return order_line.tax_rate


def order_shipping(
    order: Order,
    manager: PluginsManager,
    lines: Iterable[OrderLine] | None = None,
    force_update: bool = False,
) -> TaxedMoney:
    """Return the shipping price of the order.

    It takes into account all plugins.
    If the prices are expired, call all order price calculation methods
    and save them in the model directly.
    """
    currency = order.currency
    order, _ = fetch_order_prices_if_expired(order, manager, lines, force_update)
    return quantize_price(order.shipping_price, currency)


def order_shipping_tax_rate(
    order: Order,
    manager: PluginsManager,
    lines: Iterable[OrderLine] | None = None,
    force_update: bool = False,
) -> Decimal | None:
    """Return the shipping tax rate of the order.

    It takes into account all plugins.
    If the prices are expired, call all order price calculation methods
    and save them in the model directly.
    """
    order, _ = fetch_order_prices_if_expired(order, manager, lines, force_update)
    return order.shipping_tax_rate


def order_subtotal(
    order: Order,
    manager: PluginsManager,
    lines: Iterable[OrderLine],
    force_update: bool = False,
):
    """Return the total price of the order.

    It takes into account all plugins.
    If the prices are expired, call all order price calculation methods
    and save them in the model directly.
    """
    currency = order.currency
    order, lines = fetch_order_prices_if_expired(order, manager, lines, force_update)
    # Lines aren't returned only if
    # we don't pass them to `fetch_order_prices_if_expired`.
    return quantize_price(order.subtotal, currency)


def order_total(
    order: Order,
    manager: PluginsManager,
    lines: Iterable[OrderLine] | None = None,
    force_update: bool = False,
) -> TaxedMoney:
    """Return the total price of the order.

    It takes into account all plugins.
    If the prices are expired, call all order price calculation methods
    and save them in the model directly.
    """
    currency = order.currency
    order, _ = fetch_order_prices_if_expired(order, manager, lines, force_update)
    return quantize_price(order.total, currency)


def order_undiscounted_total(
    order: Order,
    manager: PluginsManager,
    lines: Iterable[OrderLine] | None = None,
    force_update: bool = False,
) -> TaxedMoney:
    """Return the undiscounted total price of the order.

    It takes into account all plugins.
    If the prices are expired, call all order price calculation methods
    and save them in the model directly.
    """
    currency = order.currency
    order, _ = fetch_order_prices_if_expired(order, manager, lines, force_update)
    return quantize_price(order.undiscounted_total, currency)
