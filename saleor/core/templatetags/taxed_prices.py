from django import template
from prices import MoneyRange, TaxedMoney, TaxedMoneyRange

from ...core.taxes import get_display_price

register = template.Library()


@register.inclusion_tag("product/_price_range.html", takes_context=True)
def price_range(context, price_range):
    display_gross = context["site"].settings.display_gross_prices
    return {"display_gross": display_gross, "price_range": price_range}


@register.simple_tag
def tax_rate(request, product):
    """Return tax rate value for given tax rate type in current country."""
    extensions = request.extensions
    return extensions.get_tax_rate_percentage_value(product, request.country)


@register.inclusion_tag("price.html", takes_context=True)
def price(context, base, display_gross=None, html=True):
    if isinstance(base, (TaxedMoney, TaxedMoneyRange)):
        if display_gross is None:
            display_gross = context["site"].settings.display_gross_prices

        base = get_display_price(base, display_gross)

    is_range = isinstance(base, MoneyRange)
    return {"price": base, "is_range": is_range, "html": html}
