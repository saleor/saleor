from decimal import Decimal
from typing import TYPE_CHECKING, Iterable, Optional

from prices import TaxedMoney

from ...checkout import base_calculations
from ...core.prices import quantize_price
from ...core.taxes import zero_taxed_money
from ...core.utils.country import get_active_country
from ..models import TaxClassCountryRate
from ..utils import get_tax_rate_for_tax_class, normalize_tax_rate_for_db
from . import calculate_flat_rate_tax

if TYPE_CHECKING:
    from ...account.models import Address
    from ...checkout.fetch import CheckoutInfo, CheckoutLineInfo
    from ...checkout.models import Checkout


def update_checkout_prices_with_flat_rates(
    checkout: "Checkout",
    checkout_info: "CheckoutInfo",
    lines: Iterable["CheckoutLineInfo"],
    prices_entered_with_tax: bool,
    address: Optional["Address"] = None,
):
    country_code = get_active_country(checkout_info.channel, address)
    default_country_rate_obj = TaxClassCountryRate.objects.filter(
        country=country_code, tax_class=None
    ).first()
    default_tax_rate = (
        default_country_rate_obj.rate if default_country_rate_obj else Decimal(0)
    )
    currency = checkout.currency

    # Calculate checkout line totals.
    for line_info in lines:
        line = line_info.line
        tax_class = line_info.tax_class
        tax_rate = get_tax_rate_for_tax_class(
            tax_class,
            tax_class.country_rates.all() if tax_class else [],
            default_tax_rate,
            country_code,
        )
        line_total_price = calculate_checkout_line_total(
            checkout_info,
            lines,
            line_info,
            tax_rate,
            prices_entered_with_tax,
        )
        line.total_price = line_total_price
        line.tax_rate = normalize_tax_rate_for_db(tax_rate)

    # Calculate shipping price.
    shipping_method = checkout_info.delivery_method_info.delivery_method
    tax_class = getattr(shipping_method, "tax_class", None)
    shipping_tax_rate = get_tax_rate_for_tax_class(
        tax_class,
        tax_class.country_rates.all() if tax_class else [],
        default_tax_rate,
        country_code,
    )
    shipping_price = calculate_checkout_shipping(
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


def calculate_checkout_shipping(
    checkout_info: "CheckoutInfo",
    lines: Iterable["CheckoutLineInfo"],
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


def calculate_checkout_line_total(
    checkout_info: "CheckoutInfo",
    lines: Iterable["CheckoutLineInfo"],
    checkout_line_info: "CheckoutLineInfo",
    tax_rate: Decimal,
    prices_entered_with_tax: bool,
) -> TaxedMoney:
    base_total_price = base_calculations.calculate_base_line_total_price(
        checkout_line_info,
        checkout_info.channel,
    )
    total_price = base_calculations.apply_checkout_discount_on_checkout_line(
        checkout_info,
        lines,
        checkout_line_info,
        base_total_price,
    )
    total_price = calculate_flat_rate_tax(
        total_price, tax_rate, prices_entered_with_tax
    )
    return quantize_price(total_price, total_price.currency)
