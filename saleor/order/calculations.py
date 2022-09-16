from decimal import Decimal
from typing import TYPE_CHECKING, Iterable, Optional, Tuple

from django.db import transaction
from django.db.models import prefetch_related_objects
from prices import Money, TaxedMoney

from ..checkout import base_calculations
from ..core.prices import quantize_price
from ..core.taxes import TaxData, TaxError, zero_taxed_money
from ..order import base_calculations as base_order_calculations
from ..plugins.manager import PluginsManager
from ..site.models import Site
from . import ORDER_EDITABLE_STATUS
from .interface import OrderTaxedPricesData
from .models import Order, OrderLine

if TYPE_CHECKING:
    from ..site.models import SiteSettings


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

    # Plugins like Vatlayer don't implement Order line calculation instead of implement
    # `update_taxes_for_order_lines`
    manager.update_taxes_for_order_lines(order, list(lines))

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

    for line in lines:
        variant = line.variant
        if variant:
            try:
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

                line_total = base_order_calculations.base_order_line_total(line)
                line_total.price_with_discounts = quantize_price(
                    line_total.price_with_discounts, currency
                )
                line_total.undiscounted_price = quantize_price(
                    line_total.undiscounted_price, currency
                )

                line.undiscounted_total_price = line_total.undiscounted_price
                undiscounted_subtotal += line_total.undiscounted_price
                line.total_price = line_total.price_with_discounts

                line.tax_rate = base_calculations.base_tax_rate(line.unit_price)
            except TaxError:
                pass

    try:
        shipping_price = base_order_calculations.base_order_shipping(order)
        order.shipping_price = quantize_price(
            TaxedMoney(net=shipping_price, gross=shipping_price),
            shipping_price.currency,
        )
        order.shipping_tax_rate = base_calculations.base_tax_rate(order.shipping_price)
    except TaxError:
        pass

    order.undiscounted_total = undiscounted_subtotal + order.shipping_price

    total = base_order_calculations.base_order_total(order, lines)
    order.total = quantize_price(TaxedMoney(total, total), currency)


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


def fetch_order_prices_if_expired(
    order: Order,
    manager: PluginsManager,
    lines: Optional[Iterable[OrderLine]] = None,
    force_update: bool = False,
    site_settings: "SiteSettings" = None,
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

    if site_settings is None:
        site_settings = Site.objects.get_current().settings

    if lines is None:
        lines = list(order.lines.select_related("variant__product__product_type"))
    else:
        prefetch_related_objects(lines, "variant__product__product_type")

    order.should_refresh_prices = False

    if order.tax_exemption and not site_settings.include_taxes_in_prices:
        _get_order_base_prices(order, lines)
    else:
        _recalculate_order_prices(manager, order, lines)

        tax_data = manager.get_taxes_for_order(order)

        if tax_data:
            _apply_tax_data(order, lines, tax_data)

        if order.tax_exemption and site_settings.include_taxes_in_prices:
            _exempt_taxes_in_order(order, lines)

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


def _exempt_taxes_in_order(order, lines):
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
