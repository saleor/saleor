from django import template

register = template.Library()


@register.filter
def undiscounted_price(item):
    return item.get_price(discounted=False)


@register.filter
def price_difference(price1, price2):
    return price1 - price2
