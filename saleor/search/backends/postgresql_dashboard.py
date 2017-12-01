from django.contrib.postgres.search import SearchVector

from ...product.models import Product
from ...order.models import Order
from ...userprofile.models import User


def search_products(phrase):
    '''Dashboard full text product search'''
    sv = SearchVector('name', 'description')
    return Product.objects.annotate(search=sv).filter(search=phrase)


def search_orders(phrase):
    '''Dashboard full text order search

    When phrase is convertable to int, no full text search is performed,
    just order with according id is looked up.

    '''
    try:
        order_id = int(phrase.strip())
        return Order.objects.filter(id=order_id)
    except ValueError:
        pass

    sv = SearchVector('user__default_shipping_address__first_name',
                      'user__default_shipping_address__last_name',
                      'user__email')
    return Order.objects.annotate(search=sv).filter(search=phrase)


def search_users(phrase):
    '''Dashboard full text user search'''
    sv = SearchVector('email',
                      'default_billing_address__first_name',
                      'default_billing_address__last_name')
    return User.objects.annotate(search=sv).filter(search=phrase)


def search(phrase):
    '''Dashboard full text postgres products, orders and users search

    Composes independent search querysets into dictionary result.

    Args:
        phrase (str): searched phrase

    '''
    return {'products': search_products(phrase),
            'orders': search_orders(phrase),
            'users': search_users(phrase)}
