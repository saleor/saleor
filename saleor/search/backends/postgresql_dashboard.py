from django.contrib.postgres.search import TrigramSimilarity
from django.db.models import Q
from django.contrib.postgres.search import SearchVector

from ...product.models import Product
from ...order.models import Order
from ...userprofile.models import User


def search_products(phrase):
    sv = SearchVector('name', 'description')
    return Product.objects.annotate(search=sv).filter(search=phrase)


def search_orders(phrase):
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
    sv = SearchVector('email',
                      'default_billing_address__first_name',
                      'default_billing_address__last_name')
    return User.objects.annotate(search=sv).filter(search=phrase)


def search(phrase):
    return {'products': search_products(phrase),
            'orders': search_orders(phrase),
            'users': search_users(phrase)}
