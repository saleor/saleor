from collections import defaultdict
from collections.abc import Iterable
from decimal import Decimal
from typing import TYPE_CHECKING, Optional, cast

from django.conf import settings
from prices import TaxedMoney

from ...core.prices import quantize_price
from ...core.taxes import TaxDataError, zero_taxed_money
from ...order import base_calculations
from ..models import TaxClassCountryRate
from ..utils import (
    denormalize_tax_rate_from_db,
    get_configured_zero_rated_export_tax_class_pk,
    get_shipping_tax_rate_for_order,
    get_tax_country_for_order,
    get_zero_rated_export_tax_class,
    normalize_tax_rate_for_db,
)
from . import calculate_flat_rate_tax

if TYPE_CHECKING:
    from ...order.models import Order, OrderLine
    from ...tax.models import TaxClass


def update_order_prices_with_flat_rates(
    order: "Order",
    lines: Iterable["OrderLine"],
    prices_entered_with_tax: bool,
    database_connection_name: str = settings.DATABASE_CONNECTION_DEFAULT_NAME,
):
    export_tax_class = get_zero_rated_export_tax_class(order)
    if export_tax_class is not None:
        country_code = order.channel.default_country.code
    else:
        country_code = get_tax_country_for_order(order)

    # When not in export mode, detect any stale zero-rated export class that was
    # written to lines/shipping during a prior non-DDP run and persisted to the DB.
    # Restore shipping's tax class from the shipping method (its natural source).
    stale_export_class_pk: int | None = None
    if export_tax_class is None:
        stale_export_class_pk = get_configured_zero_rated_export_tax_class_pk()
        if (
            stale_export_class_pk
            and order.shipping_tax_class_id == stale_export_class_pk
        ):
            shipping_method = order.shipping_method
            order.shipping_tax_class = (
                shipping_method.tax_class if shipping_method else None
            )

    default_country_rate_obj = (
        TaxClassCountryRate.objects.using(database_connection_name)
        .filter(country=country_code, tax_class=None)
        .first()
    )
    default_tax_rate = (
        default_country_rate_obj.rate if default_country_rate_obj else Decimal(0)
    )

    # Calculate order line taxes.
    try:
        _, undiscounted_subtotal = update_taxes_for_order_lines(
            order,
            lines,
            country_code,
            default_tax_rate,
            prices_entered_with_tax,
            export_tax_class=export_tax_class,
            stale_export_class_pk=stale_export_class_pk,
            database_connection_name=database_connection_name,
        )
    except ValueError as e:
        raise TaxDataError(str(e)) from e

    # Calculate order shipping.
    if export_tax_class:
        order.shipping_tax_class = export_tax_class
    shipping_tax_rate = get_shipping_tax_rate_for_order(
        order,
        lines,
        default_tax_rate,
        country_code,
        shipping_tax_class_id_override=export_tax_class.pk
        if export_tax_class
        else None,
        database_connection_name=database_connection_name,
    )

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
        order.undiscounted_base_shipping_price,
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
    shipping_price = (
        order.shipping_price_gross
        if prices_entered_with_tax
        else order.shipping_price_net
    )
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
    export_tax_class: Optional["TaxClass"] = None,
    stale_export_class_pk: int | None = None,
    database_connection_name: str = settings.DATABASE_CONNECTION_DEFAULT_NAME,
) -> tuple[Iterable["OrderLine"], TaxedMoney]:
    currency = order.currency
    lines = list(lines)

    undiscounted_subtotal = zero_taxed_money(order.currency)

    # Restore any stale zero-rated export class on lines from a prior non-DDP run.
    # This must happen before building the tax_class_ids set so the restored IDs
    # are included in the rates lookup.
    if not export_tax_class and stale_export_class_pk:
        for line in lines:
            if line.variant and line.tax_class_id == stale_export_class_pk:
                line.tax_class_id = line.variant.product.tax_class_id

    if export_tax_class:
        export_tax_class_rates = list(
            TaxClassCountryRate.objects.using(database_connection_name).filter(
                tax_class=export_tax_class
            )
        )
        tax_rates_per_tax_class_ic: dict[int, list[TaxClassCountryRate]] = {
            export_tax_class.pk: export_tax_class_rates
        }
    else:
        tax_class_ids: set[int] = {
            line.tax_class_id for line in lines if line.tax_class_id is not None
        }
        tax_rates_per_tax_class_ic = defaultdict(list)
        for rate in TaxClassCountryRate.objects.using(database_connection_name).filter(
            tax_class_id__in=tax_class_ids
        ):
            rate_tax_class_id = cast(int, rate.tax_class_id)
            tax_rates_per_tax_class_ic[rate_tax_class_id].append(rate)

    for line in lines:
        variant = line.variant
        if not variant:
            continue

        if export_tax_class:
            line.tax_class = export_tax_class

        tax_rate = default_tax_rate
        tax_class_id = export_tax_class.pk if export_tax_class else line.tax_class_id
        if tax_class_id:
            rates_for_class = tax_rates_per_tax_class_ic.get(tax_class_id, [])
            country_rate = next(
                (r for r in rates_for_class if r.country == country_code), None
            )
            if country_rate is None:
                raise ValueError(
                    f"No TaxClassCountryRate for country '{country_code}'"
                    f" on tax_class_id={tax_class_id}"
                )
            tax_rate = country_rate.rate
        elif line.tax_class_name is not None and line.tax_rate is not None:
            # If tax_class is None but tax_class_name is set, the tax class was set
            # for this line before, but is now removed from the system. In this case
            # try to use line.tax_rate which stores the denormalized tax rate value
            # that was originally provided by the tax class.
            tax_rate = denormalize_tax_rate_from_db(line.tax_rate)

        undiscounted_subtotal += line.undiscounted_base_unit_price * line.quantity
        price_with_discounts = (
            line.unit_price.gross if prices_entered_with_tax else line.unit_price.net
        )
        unit_price = calculate_flat_rate_tax(
            price_with_discounts, tax_rate, prices_entered_with_tax
        )
        undiscounted_unit_price = calculate_flat_rate_tax(
            line.undiscounted_base_unit_price, tax_rate, prices_entered_with_tax
        )

        line.unit_price = quantize_price(unit_price, currency)
        line.undiscounted_unit_price = quantize_price(undiscounted_unit_price, currency)

        line.total_price = quantize_price(line.unit_price * line.quantity, currency)
        line.undiscounted_total_price = quantize_price(
            line.undiscounted_unit_price * line.quantity, currency
        )
        line.tax_rate = normalize_tax_rate_for_db(tax_rate)

    return lines, undiscounted_subtotal
