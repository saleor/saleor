from decimal import Decimal
from typing import Iterable, Optional

from django.conf import settings
from django.utils import timezone
from prices import Money, TaxedMoney

from saleor.core.prices import quantize_price
from saleor.core.taxes import TaxData
from saleor.order.models import Order, OrderLine
from saleor.plugins.manager import PluginsManager


def _apply_tax_data_from_plugins(
    manager: PluginsManager, order: Order, lines: Iterable[OrderLine]
):
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
    order: Order, order_lines: Iterable[OrderLine], tax_data: TaxData
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
    zipped_order_and_tax_lines = ((line, tax_lines[line.id]) for line in order_lines)

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
) -> Order:
    import sys

    if not force_update and order.price_expiration_for_unconfirmed < timezone.now():
        print("not okay", file=sys.stderr)
        return order
    print("okay", file=sys.stderr)

    if lines is None:
        lines = list(order.lines.all())

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

    return order


def order_line_unit(
    order: Order,
    line: OrderLine,
    manager: PluginsManager,
    order_lines: Optional[Iterable[OrderLine]] = None,
    force_update: bool = False,
) -> TaxedMoney:
    return (
        fetch_order_prices_if_expired(order, manager, order_lines, force_update)
        .lines.get(pk=line.pk)
        .unit_price
    )


def order_line_total(
    order: Order,
    line: OrderLine,
    manager: PluginsManager,
    order_lines: Optional[Iterable[OrderLine]] = None,
    force_update: bool = False,
) -> TaxedMoney:
    return (
        fetch_order_prices_if_expired(order, manager, order_lines, force_update)
        .lines.get(pk=line.pk)
        .total_price
    )


def order_shipping(
    order: Order,
    manager: PluginsManager,
    order_lines: Optional[Iterable[OrderLine]] = None,
    force_update: bool = False,
) -> TaxedMoney:
    return fetch_order_prices_if_expired(
        order, manager, order_lines, force_update
    ).shipping_price
