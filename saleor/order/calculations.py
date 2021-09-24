from typing import Optional, TypedDict

from django.conf import settings
from django.utils import timezone
from prices import Money, TaxedMoney

from saleor.core.prices import quantize_price
from saleor.core.taxes import TaxData, TaxError, TaxLineData, zero_taxed_money
from saleor.order.models import Order, OrderLine
from saleor.plugins.manager import PluginsManager
from saleor.product.models import Product, ProductVariant


def order_line_total(
    *,
    manager: PluginsManager,
    order: Order,
    order_line: OrderLine,
) -> TaxedMoney:
    return (
        fetch_order_prices_if_expired(manager, order)
        .lines.get(pk=order_line.pk)
        .total_price
    )


def order_line_unit_price(
    *,
    manager: PluginsManager,
    order: Order,
    order_line: OrderLine,
) -> TaxedMoney:
    return (
        fetch_order_prices_if_expired(manager, order)
        .lines.get(pk=order_line.pk)
        .unit_price
    )


def order_shipping(
    *,
    manager: PluginsManager,
    order: Order,
) -> TaxedMoney:
    return fetch_order_prices_if_expired(
        manager,
        order,
    ).shipping_price


def fetch_order_prices_if_expired(
    manager: PluginsManager,
    order: Order,
    force_update: bool = False,
) -> Order:

    if not force_update and order.price_expiration_for_unconfirmed < timezone.now():
        return order

    plugins_tax_data = _get_tax_data_from_plugins(order, manager)

    webhooks_tax_data = manager.get_taxes_for_order(order)

    if webhooks_tax_data:
        _apply_tax_data(order, webhooks_tax_data)
    elif plugins_tax_data:
        _apply_tax_data(order, plugins_tax_data)

    return order


def _get_tax_data_from_plugins(
    order: Order,
    manager: PluginsManager,
) -> Optional[TaxData]:
    class ManagerCalculateKwargs(TypedDict):
        order: Order
        order_line: OrderLine
        variant: ProductVariant
        product: Product

    # TODO: fix this
    def manager_calculate_kwargs(order_line: OrderLine) -> ManagerCalculateKwargs:
        return {
            "order": order,
            "order_line": order_line,
            "variant": order_line.variant,  # type: ignore
            "product": order_line.variant.product,  # type: ignore
        }

    def get_line_total(order_line: OrderLine) -> TaxedMoney:
        return manager.calculate_order_line_total(
            **manager_calculate_kwargs(order_line)
        )

    def get_line_unit_price(order_line: OrderLine) -> TaxedMoney:
        return manager.calculate_order_line_unit(**manager_calculate_kwargs(order_line))

    try:
        tax_lines = [
            TaxLineData(
                id=0,
                currency=order.currency,
                total_net_amount=(total := get_line_total(line_info)).net.amount,
                total_gross_amount=total.gross.amount,
                unit_net_amount=(
                    unit_price := get_line_unit_price(line_info)
                ).net.amount,
                unit_gross_amount=unit_price.gross.amount,
            )
            for line_info in order.lines.all()
        ]

        shipping_price = manager.calculate_order_shipping(order)

        subtotal = sum(
            (
                TaxedMoney(
                    net=Money(tax_line.total_net_amount, order.currency),
                    gross=Money(tax_line.total_gross_amount, order.currency),
                )
                for tax_line in tax_lines
            ),
            zero_taxed_money(order.currency),
        )

        total = shipping_price + subtotal

        return TaxData(
            currency=order.currency,
            total_net_amount=total.net.amount,
            total_gross_amount=total.gross.amount,
            subtotal_net_amount=subtotal.net.amount,
            subtotal_gross_amount=subtotal.gross.amount,
            shipping_price_net_amount=shipping_price.net.amount,
            shipping_price_gross_amount=shipping_price.gross.amount,
            lines=tax_lines,
        )
    except TaxError:
        return None


def _apply_tax_data(order: Order, tax_data: TaxData) -> None:
    def QP(price):
        return quantize_price(price, order.currency)

    order.total_net_amount = QP(tax_data.total_net_amount)
    order.total_gross_amount = QP(tax_data.total_gross_amount)

    order.shipping_price_net_amount = QP(tax_data.shipping_price_net_amount)
    order.shipping_price_gross_amount = QP(tax_data.shipping_price_gross_amount)

    order.price_expiration_for_unconfirmed += settings.ORDER_PRICES_TTL
    order.save(
        update_fields=[
            "total_net_amount",
            "total_gross_amount",
            "shipping_price_net_amount",
            "shipping_price_gross_amount",
            "price_expiration_for_unconfirmed",
        ]
    )

    order_lines = order.lines.all()

    for (order_line, tax_line_data) in zip(order_lines, tax_data.lines):
        order_line.unit_price_net_amount = QP(tax_line_data.unit_net_amount)
        order_line.unit_price_gross_amount = QP(tax_line_data.unit_gross_amount)

        order_line.total_price_net_amount = QP(tax_line_data.total_net_amount)
        order_line.total_price_gross_amount = QP(tax_line_data.total_gross_amount)

    OrderLine.objects.bulk_update(
        order_lines,
        [
            "unit_price_net_amount",
            "unit_price_gross_amount",
            "total_price_net_amount",
            "total_price_gross_amount",
        ],
    )
