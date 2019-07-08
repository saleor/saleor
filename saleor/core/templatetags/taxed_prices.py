from django import template
from prices import MoneyRange, TaxedMoney, TaxedMoneyRange

from ...core.taxes import get_display_price
from ...core.taxes.vatlayer import DEFAULT_TAX_RATE_NAME

# FIXME This const variable belongs to vatlayer, we shouldn't take it directly from
# vatlayer module. This should be moved to plugin after we will introduce plugin
# architecture

register = template.Library()


@register.inclusion_tag("product/_price_range.html", takes_context=True)
def price_range(context, price_range):
    display_gross = context["site"].settings.display_gross_prices
    return {"display_gross": display_gross, "price_range": price_range}


@register.simple_tag
def tax_rate(taxes, rate_name):
    """Return tax rate value for given tax rate type in current country."""
    if not taxes:
        return 0
    tax = taxes.get(rate_name) or taxes.get(DEFAULT_TAX_RATE_NAME)
    return tax["value"]


@register.inclusion_tag("price.html", takes_context=True)
def price(context, base, display_gross=None, html=True):
    if isinstance(base, (TaxedMoney, TaxedMoneyRange)):
        if display_gross is None:
            display_gross = context["site"].settings.display_gross_prices

        base = get_display_price(base, display_gross)

    is_range = isinstance(base, MoneyRange)
    return {"price": base, "is_range": is_range, "html": html}
