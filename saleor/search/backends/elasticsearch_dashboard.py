from __future__ import unicode_literals

from ..documents import ProductDocument, OrderDocument, UserDocument
from elasticsearch_dsl.query import MultiMatch


def get_search_query(phrase):
    ''' Execute external search for all objects matching phrase  '''
    prod_query = MultiMatch(fields=['name', 'description'], query=phrase)
    products = ProductDocument.search().query(prod_query).source(False)

    users = UserDocument.search().query('match', email=phrase).source(False)

    order_query = MultiMatch(
        fields=['user_email', 'status', 'discount_name'], query=phrase)
    orders = OrderDocument.search().query(order_query).source(False)

    return products, users, orders


def search(phrase):
    return [s.to_queryset() for s in get_search_query(phrase)]
