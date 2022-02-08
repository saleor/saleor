from decimal import Decimal
from typing import Iterable, List, Optional, Tuple

from django.conf import settings
from django.db import transaction
from django.db.models import prefetch_related_objects
from django.utils import timezone
from prices import Money, TaxedMoney

from ..core.prices import quantize_price
from ..core.taxes import TaxData, TaxError, zero_taxed_money
from ..plugins.manager import PluginsManager
from . import ORDER_EDITABLE_STATUS
from .interface import OrderTaxedPricesData
from .models import Order, OrderLine


def _get_tax_data_from_manager(
    manager: PluginsManager, order: Order, lines: Iterable[OrderLine]
) -> Optional[dict]:
    """Fetch tax data from manager methods.

    :return: None if `TaxError` was raised, tax data dict otherwise.
    """
    currency = order.currency

    try:
        price_lines: List[dict] = []
        for line in lines:
            variant = line.variant
            if not variant:
                continue
            product = variant.product

            unit = manager.calculate_order_line_unit(order, line, variant, product)
            total = manager.calculate_order_line_total(order, line, variant, product)
            tax_rate = manager.get_order_line_tax_rate(
                order, product, variant, None, unit.undiscounted_price
            )

            price_lines.append({"tax_rate": tax_rate, "unit": unit, "total": total})

        subtotal = sum((line.total_price for line in lines), zero_taxed_money(currency))
        shipping_price = manager.calculate_order_shipping(order)
        shipping_tax_rate = manager.get_order_shipping_tax_rate(order, shipping_price)
        total = shipping_price + subtotal
    except TaxError:
        return None
    else:
        return {
            "total": total,
            "subtotal": subtotal,
            "shipping_price": shipping_price,
            "shipping_tax_rate": shipping_tax_rate,
            "lines": price_lines,
        }


def _apply_tax_data_from_manager(
    tax_data: dict, order: Order, lines: Iterable[OrderLine]
) -> None:
    """Apply tax data from manager methods into order and lines."""
    order.total = tax_data["total"]
    order.shipping_price = tax_data["shipping_price"]
    order.shipping_tax_rate = tax_data["shipping_tax_rate"]

    for order_line, price_line in zip(lines, tax_data["lines"]):
        unit = price_line["unit"]
        order_line.undiscounted_unit_price = unit.undiscounted_price
        order_line.unit_price = unit.price_with_discounts

        total = price_line["total"]
        order_line.undiscounted_total_price = total.undiscounted_price
        order_line.total_price = total.price_with_discounts

        order_line.tax_rate = price_line["tax_rate"]


def _apply_tax_data(
    order: Order, lines: Iterable[OrderLine], tax_data: TaxData
) -> None:
    def _quantize_price(net: Decimal, gross: Decimal) -> TaxedMoney:
        currency = order.currency
        return quantize_price(
            TaxedMoney(net=Money(net, currency), gross=Money(gross, currency)),
            currency,
        )

    order.total = _quantize_price(
        net=tax_data.total_net_amount, gross=tax_data.total_gross_amount
    )
    order.shipping_price = _quantize_price(
        net=tax_data.shipping_price_net_amount,
        gross=tax_data.shipping_price_gross_amount,
    )
    order.shipping_tax_rate = tax_data.shipping_tax_rate

    tax_lines = {line.id: line for line in tax_data.lines}
    zipped_order_and_tax_lines = ((line, tax_lines[line.id]) for line in lines)

    for (order_line, tax_line) in zipped_order_and_tax_lines:
        order_line.unit_price = _quantize_price(
            net=tax_line.unit_net_amount, gross=tax_line.unit_gross_amount
        )
        order_line.undiscounted_unit_price = (
            order_line.unit_price + order_line.unit_discount
        )

        order_line.total_price = _quantize_price(
            net=tax_line.total_net_amount, gross=tax_line.total_gross_amount
        )
        order_line.undiscounted_total_price = (
            order_line.undiscounted_unit_price * order_line.quantity
            if order_line.unit_discount
            else order_line.total_price
        )

        order_line.tax_rate = tax_line.tax_rate


def fetch_order_prices_if_expired(
    order: Order,
    manager: PluginsManager,
    lines: Optional[Iterable[OrderLine]] = None,
    force_update: bool = False,
) -> Tuple[Order, Optional[Iterable[OrderLine]]]:
    """Fetch order prices with taxes.

    First calculate and apply all order prices with taxes separately,
    then apply tax data as well if we receive one.

    Prices can be updated only if force_update == True,
    or if order price expiration time was exceeded
    (which is settings.ORDER_PRICES_TTL if the prices are not invalidated).
    """
    with transaction.atomic():
        if order.status not in ORDER_EDITABLE_STATUS:
            return order, lines

        if not force_update and order.price_expiration_for_unconfirmed > timezone.now():
            return order, lines

        if lines is None:
            lines = list(order.lines.prefetch_related("variant__product"))
        else:
            prefetch_related_objects(lines, "variant__product")

        order.price_expiration_for_unconfirmed = (
            timezone.now() + settings.ORDER_PRICES_TTL
        )

        manager_tax_data = _get_tax_data_from_manager(manager, order, lines)

        if manager_tax_data is not None:
            _apply_tax_data_from_manager(manager_tax_data, order, lines)

        tax_data = manager.get_taxes_for_order(order)

        if tax_data:
            _apply_tax_data(order, lines, tax_data)

        order.save(
            update_fields=[
                "total_net_amount",
                "total_gross_amount",
                "shipping_price_net_amount",
                "shipping_price_gross_amount",
                "shipping_tax_rate",
                "price_expiration_for_unconfirmed",
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

    It takes in account all plugins.
    If the prices are expired, calls all order price calculation methods
    and saves them in the model directly.
    """
    _, lines = fetch_order_prices_if_expired(order, manager, lines, force_update)
    order_line = _find_order_line(lines, order_line)
    return OrderTaxedPricesData(
        undiscounted_price=order_line.undiscounted_unit_price,
        price_with_discounts=order_line.unit_price,
    )


def order_line_total(
    order: Order,
    order_line: OrderLine,
    manager: PluginsManager,
    lines: Optional[Iterable[OrderLine]] = None,
    force_update: bool = False,
) -> OrderTaxedPricesData:
    """Return the total price of provided line, taxes included.

    It takes in account all plugins.
    If the prices are expired, calls all order price calculation methods
    and saves them in the model directly.
    """
    _, lines = fetch_order_prices_if_expired(order, manager, lines, force_update)
    order_line = _find_order_line(lines, order_line)
    return OrderTaxedPricesData(
        undiscounted_price=order_line.undiscounted_total_price,
        price_with_discounts=order_line.total_price,
    )


def order_line_tax_rate(
    order: Order,
    order_line: OrderLine,
    manager: PluginsManager,
    lines: Optional[Iterable[OrderLine]] = None,
    force_update: bool = False,
) -> Decimal:
    """Return the tax rate of provided line.

    It takes in account all plugins.
    If the prices are expired, calls all order price calculation methods
    and saves them in the model directly.
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

    It takes in account all plugins.
    If the prices are expired, calls all order price calculation methods
    and saves them in the model directly.
    """
    order, _ = fetch_order_prices_if_expired(order, manager, lines, force_update)
    return order.shipping_price


def order_shipping_tax_rate(
    order: Order,
    manager: PluginsManager,
    lines: Optional[Iterable[OrderLine]] = None,
    force_update: bool = False,
) -> Decimal:
    """Return the shipping tax rate of the order.

    It takes in account all plugins.
    If the prices are expired, calls all order price calculation methods
    and saves them in the model directly.
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

    It takes in account all plugins.
    If the prices are expired, calls all order price calculation methods
    and saves them in the model directly.
    """
    order, _ = fetch_order_prices_if_expired(order, manager, lines, force_update)
    return order.total


def order_undiscounted_total(
    order: Order,
    manager: PluginsManager,
    lines: Optional[Iterable[OrderLine]] = None,
    force_update: bool = False,
) -> TaxedMoney:
    """Return the total price of the order.

    It takes in account all plugins.
    If the prices are expired, calls all order price calculation methods
    and saves them in the model directly.
    """
    order, _ = fetch_order_prices_if_expired(order, manager, lines, force_update)
    return order.undiscounted_total
