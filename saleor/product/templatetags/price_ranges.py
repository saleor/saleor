from django import template

from ...core.utils import DEFAULT_TAX_RATE_NAME

register = template.Library()


@register.inclusion_tag('product/_price_range.html', takes_context=True)
def price_range(context, price_range):
    display_gross_prices = context['site'].settings.display_gross_prices
    return {
        'price_range': price_range,
        'display_gross_prices': display_gross_prices}


@register.simple_tag(takes_context=True)
def price_to_display(context, price, with_taxes=None):
    """Return price to display (gross or net) depending on settings.

    Extra with_taxes param forces return of gross (if true)
    or net (if false) price.
    """
    if with_taxes is None:
        display_gross_prices = context['site'].settings.display_gross_prices
    else:
        display_gross_prices = with_taxes
    return price.gross if display_gross_prices else price.net


@register.simple_tag()
def tax_value(taxes, tax_rate):
    """Return tax rate value for given tax rate type in current country."""
    if not taxes:
        return 0

    tax = taxes.get(tax_rate) or taxes.get(DEFAULT_TAX_RATE_NAME)
    return tax['value']
