from django import template
from prices import MoneyRange, TaxedMoney, TaxedMoneyRange

from ...core.utils import DEFAULT_TAX_RATE_NAME

register = template.Library()


@register.inclusion_tag('product/_price_range.html', takes_context=True)
def price_range(context, price_range):
    display_gross_prices = context['site'].settings.display_gross_prices
    return {
        'price_range': price_range,
        'display_gross_prices': display_gross_prices}


@register.simple_tag
def tax_rate(taxes, rate_name):
    """Return tax rate value for given tax rate type in current country."""
    if not taxes:
        return 0

    tax = taxes.get(rate_name) or taxes.get(DEFAULT_TAX_RATE_NAME)
    return tax['value']


@register.inclusion_tag('taxed_price.html', takes_context=True)
def taxed_price(context, base, display_gross=None):
    if display_gross is None:
        display_gross = context['site'].settings.display_gross_prices

    price = base

    if isinstance(base, TaxedMoneyRange):
        if display_gross:
            price = MoneyRange(start=base.start.gross, stop=base.stop.gross)
        else:
            price = MoneyRange(start=base.start.net, stop=base.stop.net)

    if isinstance(base, TaxedMoney):
        price = base.gross if display_gross else base.net

    is_range = isinstance(price, MoneyRange)
    return {'price': price, 'is_range': is_range}
