from elasticsearch_dsl.query import MultiMatch

from ..documents import OrderDocument, ProductDocument, UserDocument


def _search_products(phrase):
    prod_query = MultiMatch(
        fields=['name', 'title', 'description'],
        query=phrase,
        type='cross_fields')
    return ProductDocument.search().query(prod_query).sort('_score').source(
        False)


def _search_users(phrase):
    user_query = MultiMatch(
        fields=['user', 'email', 'first_name', 'last_name'],
        query=phrase,
        type='cross_fields',
        operator='and')
    return UserDocument.search().query(user_query).source(False)


def _search_orders(phrase):
    order_query = MultiMatch(
        fields=['user', 'first_name', 'last_name', 'discount_name'],
        query=phrase)
    return OrderDocument.search().query(order_query).source(False)


def get_search_queries(phrase):
    """Return querysets to lookup different types of objects.

    Args:
        phrase (str): searched phrase
    """
    return {
        'products': _search_products(phrase),
        'users': _search_users(phrase),
        'orders': _search_orders(phrase)}


def search(phrase):
    """Return all matching objects for dashboard views.

    Composes independent search querysets into a single dictionary.

    Args:
        phrase (str): searched phrase
    """
    return {k: s.to_queryset() for k, s in get_search_queries(phrase).items()}
