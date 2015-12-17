from __future__ import unicode_literals

from django_prices.templatetags.prices_i18n import gross
from satchless.item import InsufficientStock


def contains_unavailable_products(cart):
    try:
        [item.product.check_quantity(item.quantity) for item in cart]
    except InsufficientStock:
        return True
    return False


def remove_unavailable_products(cart):
    for item in cart:
        try:
            cart.add(item.product, quantity=item.quantity, replace=True)
        except InsufficientStock as e:
            quantity = e.item.get_stock_quantity()
            cart.add(item.product, quantity=quantity, replace=True)


def serialize_cart(cart):
    """For use in React's initial state"""
    state = {
        'subtotals': {line.product.pk: gross(line.get_total())
                      for line in cart},
        'total': 0}
    if cart:
        state['total'] = gross(cart.get_total())
    return state
