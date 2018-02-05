from django import template
from django_prices.templatetags.prices_i18n import gross
from prices import Price

register = template.Library()


@register.simple_tag
def discount_as_negative(discount, html=False):
    zero = Price(0, currency=discount.amount.currency)
    return gross(zero - discount.amount, html=html)
