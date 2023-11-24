from decimal import Decimal

from prices import Money, TaxedMoney

from ...core.prices import quantize_price


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


def get_taxed_undiscounted_price(
    undiscounted_base_price: "Money",
    price: "TaxedMoney",
    tax_rate: "Decimal",
    prices_entered_with_tax: bool,
):
    """Apply taxes to undiscounted base price.

    This function also prevents rounding difference between prices from tax-app and
    local calculations based on tax_rate that might occur in orders without discounts.
    """
    price_to_compare = price.gross if prices_entered_with_tax else price.net
    if undiscounted_base_price == price_to_compare:
        return price
    return quantize_price(
        calculate_flat_rate_tax(
            money=undiscounted_base_price,
            tax_rate=tax_rate * 100,
            prices_entered_with_tax=prices_entered_with_tax,
        ),
        undiscounted_base_price.currency,
    )
