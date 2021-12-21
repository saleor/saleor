from decimal import Decimal
from typing import Iterable, Optional, Tuple

from django.conf import settings
from django.db.models import prefetch_related_objects
from django.utils import timezone
from prices import Money, TaxedMoney

from ..core.prices import quantize_price
from ..core.taxes import TaxData
from ..plugins.manager import PluginsManager
from . import ORDER_EDITABLE_STATUS
from .models import Order, OrderLine


def _apply_tax_data_from_plugins(
    manager: PluginsManager, order: Order, lines: Iterable[OrderLine]
):
    prefetch_related_objects(lines, "variant__product")

    for line in lines:
        variant = line.variant
        if not variant:
            continue
        product = variant.product

        line.unit_price = manager.calculate_order_line_unit(
            order, line, variant, product
        )
        line.total_price = manager.calculate_order_line_total(
            order, line, variant, product
        )
        line.tax_rate = manager.get_order_line_tax_rate(
            order, product, variant, None, line.unit_price
        )

    order.shipping_price = manager.calculate_order_shipping(order)
    order.shipping_tax_rate = manager.get_order_shipping_tax_rate(
        order, order.shipping_price
    )
    order.total = order.shipping_price + order.get_subtotal()


def _apply_tax_data(
    order: Order, lines: Iterable[OrderLine], tax_data: TaxData
) -> None:
    def qp(net: Decimal, gross: Decimal) -> TaxedMoney:
        currency = order.currency
        return quantize_price(
            TaxedMoney(net=Money(net, currency), gross=Money(gross, currency)),
            currency,
        )

    order.total = qp(net=tax_data.total_net_amount, gross=tax_data.total_gross_amount)
    order.shipping_price = qp(
        net=tax_data.shipping_price_net_amount,
        gross=tax_data.shipping_price_gross_amount,
    )
    order.shipping_tax_rate = tax_data.shipping_tax_rate

    tax_lines = {line.id: line for line in tax_data.lines}
    zipped_order_and_tax_lines = ((line, tax_lines[line.id]) for line in lines)

    for (order_line, tax_line) in zipped_order_and_tax_lines:
        order_line.unit_price = qp(
            net=tax_line.unit_net_amount, gross=tax_line.unit_gross_amount
        )
        order_line.total_price = qp(
            net=tax_line.total_net_amount, gross=tax_line.total_gross_amount
        )
        order_line.tax_rate = tax_line.tax_rate


def fetch_order_prices_if_expired(
    order: Order,
    manager: PluginsManager,
    lines: Optional[Iterable[OrderLine]] = None,
    force_update: bool = False,
) -> Tuple[Order, Iterable[OrderLine]]:
    """Fetch order prices with taxes.

    First calculate and apply all order prices with taxes separately,
    then apply tax data as well if we receive one.

    Prices can be updated only if force_update == True,
    or if order price expiration time was exceeded
    (which is settings.ORDER_PRICES_TTL if the prices are not invalidated).
    """
    if lines is None:
        lines = list(order.lines.all())

    if order.status not in ORDER_EDITABLE_STATUS:
        return order, lines

    if not force_update and order.price_expiration_for_unconfirmed < timezone.now():
        return order, lines

    _apply_tax_data_from_plugins(manager, order, lines)

    tax_data = manager.get_taxes_for_order(order)

    if tax_data:
        _apply_tax_data(order, lines, tax_data)

    order.price_expiration_for_unconfirmed = timezone.now() + settings.ORDER_PRICES_TTL

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
            "total_price_net_amount",
            "total_price_gross_amount",
            "tax_rate",
        ],
    )

    return order, lines


def _find_order_line(
    lines: Iterable[OrderLine],
    order_line: OrderLine,
) -> OrderLine:
    """Return order line from provided lines.

    The return value represents the updated version of order_line parameter.
    """
    return next(line for line in lines if line.pk == order_line.pk)


def order_line_unit(
    order: Order,
    order_line: OrderLine,
    manager: PluginsManager,
    lines: Optional[Iterable[OrderLine]] = None,
    force_update: bool = False,
) -> TaxedMoney:
    """Return the unit price of provided line, taxes included.

    It takes in account all plugins.
    If the prices are expired, calls all order price calculation methods
    and saves them in the model directly.
    """
    _, lines = fetch_order_prices_if_expired(order, manager, lines, force_update)
    order_line = _find_order_line(lines, order_line)
    return order_line.unit_price


def order_line_total(
    order: Order,
    order_line: OrderLine,
    manager: PluginsManager,
    lines: Optional[Iterable[OrderLine]] = None,
    force_update: bool = False,
) -> TaxedMoney:
    """Return the total price of provided line, taxes included.

    It takes in account all plugins.
    If the prices are expired, calls all order price calculation methods
    and saves them in the model directly.
    """
    _, lines = fetch_order_prices_if_expired(order, manager, lines, force_update)
    order_line = _find_order_line(lines, order_line)
    return order_line.total_price


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
