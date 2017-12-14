from django import template

register = template.Library()


@register.filter
def discounted_price(item, discounts):
    return item.get_price(discounts=discounts)


@register.filter
def discounted_price_range(item, discounts):
    return item.get_price_range(discounts=discounts)


@register.filter
def price_difference(price1, price2):
    return price1 - price2
