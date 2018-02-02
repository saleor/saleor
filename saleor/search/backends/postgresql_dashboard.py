from django.contrib.postgres.search import (
    SearchQuery, SearchRank, SearchVector)

from ...order.models import Order
from ...product.models import Product
from ...userprofile.models import User


def search_products(phrase):
    """Return matching products for dashboard views."""
    sv = (SearchVector('name', weight='A') +
          SearchVector('description', weight='B'))
    rank = SearchRank(sv, SearchQuery(phrase))
    return Product.objects.annotate(rank=rank).filter(
        rank__gte=0.2).order_by('-rank')


def search_orders(phrase):
    """Return matching orders for dashboard views.

    When phrase is convertable to int, no full text search is performed,
    just order with matching id is looked up.
    """
    try:
        order_id = int(phrase.strip())
        return Order.objects.filter(id=order_id)
    except ValueError:
        pass

    sv = (
        SearchVector(
            'user__default_shipping_address__first_name', weight='B') +
        SearchVector('user__default_shipping_address__last_name', weight='B') +
        SearchVector('user__email', weight='A'))
    rank = SearchRank(sv, SearchQuery(phrase))
    return Order.objects.annotate(rank=rank).filter(
        rank__gte=0.2).order_by('-rank')


def search_users(phrase):
    """Return matching users for dashboard views."""
    sv = (SearchVector('email', weight='A') +
          SearchVector('default_billing_address__first_name', weight='B') +
          SearchVector('default_billing_address__last_name', weight='B'))
    rank = SearchRank(sv, SearchQuery(phrase))
    return User.objects.annotate(rank=rank).filter(
        rank__gte=0.2).order_by('-rank')


def search(phrase):
    """Return all matching objects for dashboard views.

    Composes independent search querysets into a single dictionary.

    Args:
        phrase (str): searched phrase
    """
    return {
        'products': search_products(phrase),
        'orders': search_orders(phrase),
        'users': search_users(phrase)}
