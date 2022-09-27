from decimal import Decimal
from typing import TYPE_CHECKING, Iterable, Optional

from prices import Money, TaxedMoney

from ..checkout import base_calculations
from ..core.prices import quantize_price
from ..core.taxes import TaxData, TaxLineData
from ..discount import DiscountInfo
from ..shipping.interface import ShippingMethodData
from .models import TaxClassCountryRate

if TYPE_CHECKING:
    from ..account.models import Address
    from ..checkout.fetch import CheckoutInfo, CheckoutLineInfo


def get_flat_rates_tax_data_for_checkout(
    checkout_info: "CheckoutInfo",
    lines: Iterable["CheckoutLineInfo"],
    prices_entered_with_tax: bool,
    address: Optional["Address"] = None,
    discounts: Optional[Iterable[DiscountInfo]] = None,
) -> "TaxData":
    country_code = (
        address.country.code if address else checkout_info.channel.default_country.code
    )
    default_country_rate_obj = TaxClassCountryRate.objects.filter(
        tax_class=None
    ).first()
    default_country_rate = (
        default_country_rate_obj.rate if default_country_rate_obj else Decimal(0)
    )

    lines_with_flat_rate_tax = [
        _calculate_line_totals_with_flat_rate_tax(
            checkout_info,
            line_info,
            country_code,
            default_country_rate,
            prices_entered_with_tax,
            discounts,
        )
        for line_info in lines
    ]

    shipping_price_taxed = _calculate_shipping_with_flat_rate_tax(
        checkout_info,
        lines,
        country_code,
        default_country_rate,
        prices_entered_with_tax,
    )

    return TaxData(
        shipping_price_gross_amount=shipping_price_taxed.total_gross_amount,
        shipping_price_net_amount=shipping_price_taxed.total_net_amount,
        shipping_tax_rate=shipping_price_taxed.tax_rate,
        lines=lines_with_flat_rate_tax,
    )


def _calculate_flat_rate_tax(
    money: "Money", tax_rate: "Decimal", prices_entered_with_tax: bool
) -> TaxedMoney:
    currency = money.currency
    tax_rate = Decimal(1 + tax_rate / 100)

    if prices_entered_with_tax:
        net_amount = quantize_price(money.amount / tax_rate, currency)
        gross_amount = money.amount
    else:
        net_amount = money.amount
        gross_amount = quantize_price(money.amount * tax_rate, currency)
    return TaxedMoney(
        net=Money(net_amount, currency), gross=Money(gross_amount, currency)
    )


def _calculate_line_totals_with_flat_rate_tax(
    checkout_info: "CheckoutInfo",
    line_info: "CheckoutLineInfo",
    country_code: str,
    default_country_rate: "Decimal",
    prices_entered_with_tax: bool,
    discounts: Optional[Iterable[DiscountInfo]] = None,
) -> TaxLineData:
    tax_class = line_info.tax_class

    tax_rate = default_country_rate
    if tax_class:
        for country_rate in tax_class.country_rates.all():
            if country_rate.country == country_code:
                tax_rate = country_rate.rate

    total_price_default = base_calculations.calculate_base_line_total_price(
        line_info,
        checkout_info.channel,
        discounts,
    )
    total_price_taxed = _calculate_flat_rate_tax(
        total_price_default, tax_rate, prices_entered_with_tax
    )

    return TaxLineData(
        total_gross_amount=total_price_taxed.gross.amount,
        total_net_amount=total_price_taxed.net.amount,
        tax_rate=tax_rate,
    )


def _calculate_shipping_with_flat_rate_tax(
    checkout_info: "CheckoutInfo",
    lines: Iterable["CheckoutLineInfo"],
    country_code: str,
    default_country_rate: "Decimal",
    prices_entered_with_tax: bool,
) -> TaxLineData:

    shipping_method = checkout_info.delivery_method_info.delivery_method
    if not isinstance(shipping_method, ShippingMethodData):
        return TaxLineData(
            tax_rate=Decimal(0),
            total_gross_amount=Decimal(0),
            total_net_amount=Decimal(0),
        )

    tax_rate = default_country_rate
    tax_class = shipping_method.tax_class
    if tax_class:
        for country_rate in tax_class.country_rates.all():
            if country_rate.country == country_code:
                tax_rate = country_rate.rate

    shipping_price_default = base_calculations.base_checkout_delivery_price(
        checkout_info, lines
    )
    shipping_price_taxed = _calculate_flat_rate_tax(
        shipping_price_default, tax_rate, prices_entered_with_tax
    )
    return TaxLineData(
        tax_rate=tax_rate,
        total_gross_amount=shipping_price_taxed.gross.amount,
        total_net_amount=shipping_price_taxed.net.amount,
    )
