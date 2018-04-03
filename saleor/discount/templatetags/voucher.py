from django import template
from django_prices.templatetags import prices_i18n
from prices import Money

register = template.Library()


@register.simple_tag
def discount_as_negative(discount, html=False):
    zero = Money(0, discount.currency)
    return prices_i18n.amount(zero - discount, 'html' if html else 'text')
