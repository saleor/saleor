from decimal import Decimal

from prices import Money, TaxedMoney


def calculate_flat_rate_tax(
    money: "Money", tax_rate: "Decimal", prices_entered_with_tax: bool
) -> TaxedMoney:
    currency = money.currency
    tax_rate = Decimal(1 + tax_rate / 100)

    if prices_entered_with_tax:
        net_amount = money.amount / tax_rate
        gross_amount = money.amount
    else:
        net_amount = money.amount
        gross_amount = money.amount * tax_rate
    return TaxedMoney(
        net=Money(net_amount, currency), gross=Money(gross_amount, currency)
    )
