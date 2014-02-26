from django import template

from ..utils import convert_price


register = template.Library()


@register.simple_tag()
def convert_currency(price, currency):
    converted = convert_price(price, currency)
    return converted.gross