from decimal import Decimal

from prices import Money, TaxedMoney

from ...core.prices import quantize_price


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
