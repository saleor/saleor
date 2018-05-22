from django import template
from prices import MoneyRange, TaxedMoney, TaxedMoneyRange

from ...core.utils.taxes import DEFAULT_TAX_RATE_NAME

register = template.Library()


@register.inclusion_tag('product/_price_range.html', takes_context=True)
def price_range(context, price_range):
    display_gross = context['site'].settings.display_gross_prices
    return {'display_gross': display_gross, 'price_range': price_range}


@register.simple_tag
def tax_rate(taxes, rate_name):
    """Return tax rate value for given tax rate type in current country."""
    if not taxes:
        return 0

    tax = taxes.get(rate_name) or taxes.get(DEFAULT_TAX_RATE_NAME)
    return tax['value']


@register.inclusion_tag('price.html', takes_context=True)
def price(context, base, display_gross=None, html=True):
    if isinstance(base, (TaxedMoney, TaxedMoneyRange)):
        if display_gross is None:
            display_gross = context['site'].settings.display_gross_prices

        if isinstance(base, TaxedMoneyRange):
            if display_gross:
                base = MoneyRange(start=base.start.gross, stop=base.stop.gross)
            else:
                base = MoneyRange(start=base.start.net, stop=base.stop.net)

        if isinstance(base, TaxedMoney):
            base = base.gross if display_gross else base.net

    is_range = isinstance(base, MoneyRange)
    return {'price': base, 'is_range': is_range, 'html': html}
