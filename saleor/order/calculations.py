from decimal import Decimal
from typing import Iterable, Optional, Tuple

from django.db import transaction
from django.db.models import prefetch_related_objects
from prices import Money, TaxedMoney

from ..core.prices import quantize_price
from ..core.taxes import TaxData, TaxError, zero_taxed_money
from ..discount import OrderDiscountType
from ..plugins.manager import PluginsManager
from . import ORDER_EDITABLE_STATUS, utils
from .interface import OrderTaxedPricesData
from .models import Order, OrderLine


def _recalculate_order_prices(
    manager: PluginsManager, order: Order, lines: Iterable[OrderLine]
) -> None:
    """Fetch taxes from plugins and recalculate order/lines prices.

    Does not throw TaxError.
    """
    currency = order.currency

    subtotal = zero_taxed_money(currency)
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
                line.total_price = line_total.price_with_discounts

                line.tax_rate = manager.get_order_line_tax_rate(
                    order, product, variant, None, line_unit.undiscounted_price
                )
            except TaxError:
                pass

        subtotal += line.total_price
    try:
        order.shipping_price = manager.calculate_order_shipping(order)
        order.shipping_tax_rate = manager.get_order_shipping_tax_rate(
            order, order.shipping_price
        )
    except TaxError:
        pass

    order.total = order.shipping_price + subtotal


def _apply_tax_data(
    order: Order, lines: Iterable[OrderLine], tax_data: TaxData
) -> None:
    """Apply all prices from tax data to order and order lines."""
    currency = order.currency
    shipping_price = TaxedMoney(
        net=Money(tax_data.shipping_price_net_amount, currency),
        gross=Money(tax_data.shipping_price_gross_amount, currency),
    )

    order.shipping_price = shipping_price
    # We use % value in tax app input but on database we store
    # it as a fractional value.
    # e.g Tax app sends `10%` as `10` but in database it's stored as `0.1`
    order.shipping_tax_rate = tax_data.shipping_tax_rate / 100

    subtotal = zero_taxed_money(order.currency)
    for (order_line, tax_line) in zip(lines, tax_data.lines):
        line_total_price = TaxedMoney(
            net=Money(tax_line.total_net_amount, currency),
            gross=Money(tax_line.total_gross_amount, currency),
        )
        order_line.total_price = line_total_price
        order_line.unit_price = line_total_price / order_line.quantity
        # We use % value in tax app input but on database we store
        # it as a fractional value.
        # e.g Tax app sends `10%` as `10` but in database it's stored as `0.1`
        order_line.tax_rate = tax_line.tax_rate / 100
        subtotal += line_total_price

    order.total = shipping_price + subtotal


def _recalculate_order_discounts(order: Order, lines: Iterable[OrderLine]) -> None:
    """Recalculate all order discounts and update order/lines prices."""
    undiscounted_subtotal = zero_taxed_money(order.currency)
    for line in lines:
        line.undiscounted_unit_price = line.unit_price + line.unit_discount
        undiscounted_total_price = (
            line.undiscounted_unit_price * line.quantity
            if line.unit_discount
            else line.total_price
        )
        line.undiscounted_total_price = undiscounted_total_price
        undiscounted_subtotal += undiscounted_total_price

    order.undiscounted_total = undiscounted_subtotal + order.shipping_price

    order_discounts = order.discounts.filter(type=OrderDiscountType.MANUAL)
    for order_discount in order_discounts:
        utils.update_order_discount_for_order(
            order,
            order_discount,
        )


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

    if lines is None:
        lines = list(order.lines.select_related("variant__product__product_type"))
    else:
        prefetch_related_objects(lines, "variant__product__product_type")

    order.should_refresh_prices = False

    _recalculate_order_prices(manager, order, lines)

    tax_data = manager.get_taxes_for_order(order)

    with transaction.atomic(savepoint=False):
        if tax_data:
            _apply_tax_data(order, lines, tax_data)

        _recalculate_order_discounts(order, lines)

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
) -> Decimal:
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
) -> Decimal:
    """Return the shipping tax rate of the order.

    It takes into account all plugins.
    If the prices are expired, call all order price calculation methods
    and save them in the model directly.
    """
    order, _ = fetch_order_prices_if_expired(order, manager, lines, force_update)
    return order.shipping_tax_rate


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
