from django import template
from django_prices.templatetags.prices_i18n import amount
from prices import Amount

register = template.Library()


@register.simple_tag
def discount_as_negative(discount, html=False):
    zero = Amount(0, currency=discount.amount.currency)
    return amount(zero-discount.amount, format=html)
