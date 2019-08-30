from django import template
from django_prices.templatetags import prices
from prices import Money

register = template.Library()


@register.simple_tag
def discount_as_negative(discount, html=False):
    zero = Money(0, discount.currency)
    return prices.amount(zero - discount, "html" if html else "text")
