from django import template

register = template.Library()


@register.inclusion_tag('product/_price_range.html')
def price_range(price_range):
    return {'price_range': price_range}


@register.inclusion_tag('product/_exchanged_price_range.html')
def exchanged_price_range(price_range, currency_code):
    return {'currency_code': currency_code, 'price_range': price_range}
