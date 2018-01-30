from django.template import Library

from ..utils import get_deliveries, get_total


register = Library()


@register.assignment_tag
def get_checkout_deliveries(checkout):
    return get_deliveries(checkout.cart, checkout.shipping_method)


@register.assignment_tag
def get_checkout_total(checkout):
    return get_total(
        checkout.cart, checkout.shipping_method, checkout.discount)
