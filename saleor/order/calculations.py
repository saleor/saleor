from decimal import Decimal
from typing import Iterable, Optional, Tuple, cast

from django.db import transaction
from django.db.models import prefetch_related_objects
from prices import Money, TaxedMoney

from ..core.prices import quantize_price
from ..core.taxes import TaxData, TaxError, zero_taxed_money
from ..order import base_calculations
from ..payment.model_helpers import get_subtotal
from ..plugins.manager import PluginsManager
from ..tax import TaxCalculationStrategy
from ..tax.calculations.order import update_order_prices_with_flat_rates
from ..tax.utils import (
    calculate_tax_rate,
    get_charge_taxes_for_order,
    get_tax_calculation_strategy_for_order,
    normalize_tax_rate_for_db,
)
from . import ORDER_EDITABLE_STATUS
from .interface import OrderTaxedPricesData
from .models import Order, OrderLine


def _recalculate_order_prices(
    manager: PluginsManager, order: Order, lines: Iterable[OrderLine]
) -> None:
    """Fetch taxes from plugins and recalculate order/lines prices.

    Does not throw TaxError.
    """
    undiscounted_subtotal = zero_taxed_money(order.currency)
    for line in lines:
        variant = line.variant
        if variant:
            product = variant.product

            try:
                line_unit = manager.calculate_order_line_unit(
                    order, line, variant, product
                )
                line.undiscounted_unit_price = line_unit.undiscounted_price
                line.unit_price = line_unit.price_with_discounts

                line_total = manager.calculate_order_line_total(
                    order, line, variant, product
                )
                line.undiscounted_total_price = line_total.undiscounted_price
                undiscounted_subtotal += line_total.undiscounted_price
                line.total_price = line_total.price_with_discounts

                line.tax_rate = manager.get_order_line_tax_rate(
                    order, product, variant, None, line_unit.undiscounted_price
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
    order.undiscounted_total = undiscounted_subtotal + order.shipping_price
    order.total = manager.calculate_order_total(order, lines)


def _get_order_base_prices(order, lines):
    currency = order.currency
    undiscounted_subtotal = zero_taxed_money(currency)

    # Calculate order lines prices.
    for line in lines:
        variant = line.variant
        if not variant:
            continue

        line_unit_default = OrderTaxedPricesData(
            undiscounted_price=TaxedMoney(
                line.undiscounted_base_unit_price,
                line.undiscounted_base_unit_price,
            ),
            price_with_discounts=TaxedMoney(
                line.base_unit_price,
                line.base_unit_price,
            ),
        )
        line_unit_default.price_with_discounts = quantize_price(
            line_unit_default.price_with_discounts, currency
        )
        line_unit_default.undiscounted_price = quantize_price(
            line_unit_default.undiscounted_price, currency
        )

        line.undiscounted_unit_price = line_unit_default.undiscounted_price
        line.unit_price = line_unit_default.price_with_discounts

        line_total = base_calculations.base_order_line_total(line)
        line_total.price_with_discounts = quantize_price(
            line_total.price_with_discounts, currency
        )
        line_total.undiscounted_price = quantize_price(
            line_total.undiscounted_price, currency
        )

        line.undiscounted_total_price = line_total.undiscounted_price
        undiscounted_subtotal += line_total.undiscounted_price
        line.total_price = line_total.price_with_discounts

        line.tax_rate = calculate_tax_rate(line.unit_price)

    # Calculate shipping price.
    shipping_price = order.base_shipping_price
    order.shipping_price = quantize_price(
        TaxedMoney(net=shipping_price, gross=shipping_price),
        shipping_price.currency,
    )
    order.shipping_tax_rate = calculate_tax_rate(order.shipping_price)

    # Calculate order total.
    order.undiscounted_total = undiscounted_subtotal + order.shipping_price
    total = base_calculations.base_order_total(order, lines)
    order.total = quantize_price(TaxedMoney(total, total), currency)


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
    for (order_line, tax_line) in zip(lines, tax_data.lines):
        line_total_price = TaxedMoney(
            net=Money(tax_line.total_net_amount, currency),
            gross=Money(tax_line.total_gross_amount, currency),
        )
        order_line.total_price = line_total_price
        order_line.unit_price = line_total_price / order_line.quantity
        order_line.tax_rate = normalize_tax_rate_for_db(tax_line.tax_rate)
        subtotal += line_total_price

    order.total = shipping_price + subtotal


def fetch_order_prices_if_expired(
    order: Order,
    manager: PluginsManager,
    lines: Optional[Iterable[OrderLine]] = None,
    force_update: bool = False,
) -> Tuple[Order, Optional[Iterable[OrderLine]]]:
    """Fetch order prices with taxes.

    First calculate and apply all order prices with taxes separately,
    then apply tax data as well if we receive one.

    Prices will be updated if force_update is True,
    or if order.should_refresh_prices is True.
    """
    if order.status not in ORDER_EDITABLE_STATUS:
        return order, lines

    if not force_update and not order.should_refresh_prices:
        return order, lines

    tax_configuration = order.channel.tax_configuration
    tax_calculation_strategy = get_tax_calculation_strategy_for_order(order)
    prices_entered_with_tax = tax_configuration.prices_entered_with_tax
    charge_taxes = get_charge_taxes_for_order(order)
    should_charge_tax = charge_taxes and not order.tax_exemption

    if lines is None:
        lines = list(order.lines.select_related("variant__product__product_type"))
    else:
        prefetch_related_objects(lines, "variant__product__product_type")

    order.should_refresh_prices = False

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
            # Calculate net prices without taxes.
            _get_order_base_prices(order, lines)

    with transaction.atomic(savepoint=False):
        order.save(
            update_fields=[
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


def _calculate_and_add_tax(
    tax_calculation_strategy: str,
    order: "Order",
    lines: Iterable["OrderLine"],
    manager: "PluginsManager",
    prices_entered_with_tax: bool,
):
    if tax_calculation_strategy == TaxCalculationStrategy.TAX_APP:
        _recalculate_order_prices(manager, order, lines)
        tax_data = manager.get_taxes_for_order(order)
        _apply_tax_data(order, lines, tax_data)
    elif tax_calculation_strategy == TaxCalculationStrategy.FLAT_RATES:
        update_order_prices_with_flat_rates(order, lines, prices_entered_with_tax)


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
    lines: Optional[Iterable[OrderLine]] = None,
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
    lines: Optional[Iterable[OrderLine]] = None,
    force_update: bool = False,
) -> Optional[Decimal]:
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
    lines: Optional[Iterable[OrderLine]] = None,
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
    lines: Optional[Iterable[OrderLine]] = None,
    force_update: bool = False,
) -> Optional[Decimal]:
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
    lines = cast(Iterable[OrderLine], lines)
    return quantize_price(get_subtotal(lines, currency), currency)


def order_total(
    order: Order,
    manager: PluginsManager,
    lines: Optional[Iterable[OrderLine]] = None,
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
    lines: Optional[Iterable[OrderLine]] = None,
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
