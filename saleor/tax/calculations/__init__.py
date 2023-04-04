from decimal import Decimal

from prices import Money, TaxedMoney

from saleor.core.prices import quantize_price


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


def add_tax_to_undiscounted_price(
    price: "Money", tax_rate: "Decimal", prices_entered_with_tax: bool
) -> TaxedMoney:
    currency = price.currency
    # multiply tax_rate to reuse calculate_flat_rate_tax that is originally using ints
    # instead of Decimals.
    taxed_price = calculate_flat_rate_tax(
        price, (tax_rate*100), prices_entered_with_tax
    )
    return TaxedMoney(
        net=quantize_price(taxed_price.net, currency),
        gross=quantize_price(taxed_price.gross, currency)
    )
