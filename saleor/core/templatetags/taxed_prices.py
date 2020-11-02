from django import template
from prices import Money, MoneyRange, TaxedMoney, TaxedMoneyRange

from ...core.taxes import get_display_price

register = template.Library()


@register.inclusion_tag("price.html", takes_context=True)
def price_amount(context, net_amount, gross_amount, currency, display_gross, html=True):
    amount = net_amount
    if display_gross:
        amount = gross_amount
    if not currency:
        currency = context.get("currency")
    return {
        "price": Money(amount=amount, currency=currency),
        "is_range": False,
        "html": html,
    }


@register.inclusion_tag("price.html", takes_context=True)
def price(context, base, display_gross=None, html=True):
    if isinstance(base, (TaxedMoney, TaxedMoneyRange)):
        if display_gross is None:
            display_gross = context["site"].settings.display_gross_prices

        base = get_display_price(base, display_gross)

    is_range = isinstance(base, MoneyRange)
    return {"price": base, "is_range": is_range, "html": html}
