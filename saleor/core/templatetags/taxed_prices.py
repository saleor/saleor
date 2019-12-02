from django import template
from prices import MoneyRange, TaxedMoney, TaxedMoneyRange

from ...core.taxes import get_display_price

register = template.Library()


@register.inclusion_tag("price.html", takes_context=True)
def price(context, base, display_gross=None, html=True):
    if isinstance(base, (TaxedMoney, TaxedMoneyRange)):
        if display_gross is None:
            display_gross = context["site"].settings.display_gross_prices

        base = get_display_price(base, display_gross)

    is_range = isinstance(base, MoneyRange)
    return {"price": base, "is_range": is_range, "html": html}
