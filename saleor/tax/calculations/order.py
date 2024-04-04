from collections.abc import Iterable
from decimal import Decimal
from typing import TYPE_CHECKING

from django.conf import settings
from prices import TaxedMoney

from ...core.prices import quantize_price
from ...core.taxes import zero_taxed_money
from ...order import base_calculations
from ...order.utils import get_order_country
from ..models import TaxClassCountryRate
from ..utils import (
    denormalize_tax_rate_from_db,
    get_tax_rate_for_tax_class,
    normalize_tax_rate_for_db,
)
from . import calculate_flat_rate_tax

if TYPE_CHECKING:
    from ...order.models import Order, OrderLine


def update_order_prices_with_flat_rates(
    order: "Order",
    lines: Iterable["OrderLine"],
    prices_entered_with_tax: bool,
    database_connection_name: str = settings.DATABASE_CONNECTION_DEFAULT_NAME,
):
    country_code = get_order_country(order)
    default_country_rate_obj = (
        TaxClassCountryRate.objects.using(database_connection_name)
        .filter(country=country_code, tax_class=None)
        .first()
    )
    default_tax_rate = (
        default_country_rate_obj.rate if default_country_rate_obj else Decimal(0)
    )

    # Calculate order line taxes.
    _, undiscounted_subtotal = update_taxes_for_order_lines(
        order, lines, country_code, default_tax_rate, prices_entered_with_tax
    )

    # Calculate order shipping.
    shipping_method = order.shipping_method
    shipping_tax_class = getattr(shipping_method, "tax_class", None)
    if shipping_tax_class:
        shipping_tax_rate = get_tax_rate_for_tax_class(
            shipping_tax_class,
            shipping_tax_class.country_rates.all(),
            default_tax_rate,
            country_code,
        )
    elif (
        order.shipping_tax_class_name is not None
        and order.shipping_tax_rate is not None
    ):
        # Use order.shipping_tax_rate if it was ever set before (it's non-null now and
        # the name is non-null). This is a valid case when recalculating shipping price
        # and the tax class is null, because it was removed from the system.
        shipping_tax_rate = denormalize_tax_rate_from_db(order.shipping_tax_rate)
    else:
        shipping_tax_rate = default_tax_rate

    order.shipping_price = _calculate_order_shipping(
        order, shipping_tax_rate, prices_entered_with_tax
    )
    order.shipping_tax_rate = normalize_tax_rate_for_db(shipping_tax_rate)

    _set_order_totals(
        order,
        lines,
        prices_entered_with_tax,
        database_connection_name=database_connection_name,
    )


def _set_order_totals(
    order: "Order",
    lines: Iterable["OrderLine"],
    prices_entered_with_tax: bool,
    database_connection_name: str = settings.DATABASE_CONNECTION_DEFAULT_NAME,
):
    currency = order.currency

    default_value = base_calculations.base_order_total(
        order, lines, database_connection_name=database_connection_name
    )
    default_value = TaxedMoney(default_value, default_value)
    if default_value <= zero_taxed_money(currency):
        order.total = quantize_price(default_value, currency)
        order.undiscounted_total = quantize_price(default_value, currency)
        order.subtotal = quantize_price(default_value, currency)
        return

    subtotal = zero_taxed_money(currency)
    undiscounted_subtotal = zero_taxed_money(currency)
    for line in lines:
        subtotal += line.total_price
        undiscounted_subtotal += line.undiscounted_total_price

    shipping_tax_rate = order.shipping_tax_rate or 0
    undiscounted_shipping_price = calculate_flat_rate_tax(
        order.base_shipping_price,
        Decimal(shipping_tax_rate * 100),
        prices_entered_with_tax,
    )
    undiscounted_total = undiscounted_subtotal + undiscounted_shipping_price

    order.total = quantize_price(subtotal + order.shipping_price, currency)
    order.undiscounted_total = quantize_price(undiscounted_total, currency)
    order.subtotal = quantize_price(subtotal, currency)


def _calculate_order_shipping(
    order: "Order", tax_rate: Decimal, prices_entered_with_tax: bool
) -> TaxedMoney:
    shipping_price = order.shipping_price.net
    taxed_shipping_price = calculate_flat_rate_tax(
        shipping_price, tax_rate, prices_entered_with_tax
    )
    return quantize_price(taxed_shipping_price, taxed_shipping_price.currency)


def update_taxes_for_order_lines(
    order: "Order",
    lines: Iterable["OrderLine"],
    country_code: str,
    default_tax_rate: Decimal,
    prices_entered_with_tax: bool,
) -> tuple[Iterable["OrderLine"], TaxedMoney]:
    currency = order.currency
    lines = list(lines)

    undiscounted_subtotal = zero_taxed_money(order.currency)

    for line in lines:
        variant = line.variant
        if not variant:
            continue

        tax_class = line.tax_class
        if tax_class:
            tax_rate = get_tax_rate_for_tax_class(
                tax_class,
                tax_class.country_rates.all() if tax_class else [],
                default_tax_rate,
                country_code,
            )
        elif line.tax_class_name is not None and line.tax_rate is not None:
            # If tax_class is None but tax_class_name is set, the tax class was set
            # for this line before, but is now removed from the system. In this case
            # try to use line.tax_rate which stores the denormalized tax rate value
            # that was originally provided by the tax class.
            tax_rate = denormalize_tax_rate_from_db(line.tax_rate)
        else:
            tax_rate = default_tax_rate

        undiscounted_subtotal += line.undiscounted_base_unit_price * line.quantity
        price_with_discounts = line.unit_price.net
        unit_price = calculate_flat_rate_tax(
            price_with_discounts, tax_rate, prices_entered_with_tax
        )
        undiscounted_unit_price = calculate_flat_rate_tax(
            line.undiscounted_base_unit_price, tax_rate, prices_entered_with_tax
        )

        line.unit_price = quantize_price(unit_price, currency)
        line.undiscounted_unit_price = quantize_price(undiscounted_unit_price, currency)

        line.total_price = quantize_price(unit_price * line.quantity, currency)
        line.undiscounted_total_price = quantize_price(
            undiscounted_unit_price * line.quantity, currency
        )
        line.tax_rate = normalize_tax_rate_for_db(tax_rate)

    return lines, undiscounted_subtotal
