from decimal import Decimal
from typing import TYPE_CHECKING

from django.conf import settings
from prices import TaxedMoney

from ...checkout import base_calculations
from ...core.prices import quantize_price
from ...core.taxes import zero_taxed_money
from ..models import TaxClassCountryRate
from ..utils import (
    get_checkout_active_country,
    get_shipping_tax_rate_for_checkout,
    get_tax_rate_for_country,
    normalize_tax_rate_for_db,
)
from . import calculate_flat_rate_tax

if TYPE_CHECKING:
    from ...checkout.fetch import CheckoutInfo, CheckoutLineInfo
    from ...checkout.models import Checkout


def update_checkout_prices_with_flat_rates(
    checkout: "Checkout",
    checkout_info: "CheckoutInfo",
    lines: list["CheckoutLineInfo"],
    prices_entered_with_tax: bool,
    database_connection_name: str = settings.DATABASE_CONNECTION_DEFAULT_NAME,
):
    country_code = get_checkout_active_country(checkout_info)
    default_country_rate_obj = (
        TaxClassCountryRate.objects.using(database_connection_name)
        .filter(country=country_code, tax_class=None)
        .first()
    )
    default_tax_rate = (
        default_country_rate_obj.rate if default_country_rate_obj else Decimal(0)
    )
    currency = checkout.currency

    # Calculate checkout line totals.
    for line_info in lines:
        line = line_info.line
        tax_class = line_info.tax_class

        tax_rate = get_tax_rate_for_country(
            tax_class.country_rates.all() if tax_class else [],
            default_tax_rate,
            country_code,
        )

        line_total_price = _calculate_checkout_line_total(
            checkout_info,
            lines,
            line_info,
            tax_rate,
            prices_entered_with_tax,
        )
        line.total_price = line_total_price
        line.tax_rate = normalize_tax_rate_for_db(tax_rate)

    # Calculate shipping details.
    shipping_tax_rate = get_shipping_tax_rate_for_checkout(
        checkout_info,
        lines,
        default_tax_rate,
        country_code,
        database_connection_name=database_connection_name,
    )
    shipping_price = _calculate_checkout_shipping(
        checkout_info, lines, shipping_tax_rate, prices_entered_with_tax
    )
    checkout.shipping_price = shipping_price
    checkout.shipping_tax_rate = normalize_tax_rate_for_db(shipping_tax_rate)

    # Calculate subtotal and total.
    subtotal = sum(
        [line_info.line.total_price for line_info in lines], zero_taxed_money(currency)
    )
    checkout.subtotal = subtotal
    checkout.total = subtotal + shipping_price


def _calculate_checkout_shipping(
    checkout_info: "CheckoutInfo",
    lines: list["CheckoutLineInfo"],
    tax_rate: Decimal,
    prices_entered_with_tax: bool,
) -> TaxedMoney:
    shipping_price = base_calculations.base_checkout_delivery_price(
        checkout_info, lines
    )
    shipping_price_taxed = calculate_flat_rate_tax(
        shipping_price, tax_rate, prices_entered_with_tax
    )
    return quantize_price(shipping_price_taxed, shipping_price_taxed.currency)


def _calculate_checkout_line_total(
    checkout_info: "CheckoutInfo",
    lines: list["CheckoutLineInfo"],
    checkout_line_info: "CheckoutLineInfo",
    tax_rate: Decimal,
    prices_entered_with_tax: bool,
) -> TaxedMoney:
    total_price = (
        base_calculations.get_line_total_price_with_propagated_checkout_discount(
            checkout_info,
            lines,
            checkout_line_info,
        )
    )
    total_price = calculate_flat_rate_tax(
        total_price, tax_rate, prices_entered_with_tax
    )
    return quantize_price(total_price, total_price.currency)
