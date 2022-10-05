from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from prices import Money, TaxedMoney

from ...core.prices import quantize_price

if TYPE_CHECKING:
    from ...tax.models import TaxClass


def calculate_flat_rate_tax(
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


def get_tax_rate_for_tax_class(
    tax_class: Optional["TaxClass"], default_tax_rate: Decimal, country_code: str
) -> Decimal:
    tax_rate = default_tax_rate
    if tax_class:
        for country_rate in tax_class.country_rates.all():
            if country_rate.country == country_code:
                tax_rate = country_rate.rate
    return tax_rate
