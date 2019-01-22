import functools
import operator

from ...product.filters import MergedAttributes
from ...product.models import Attribute


def filter_products_by_attributes(qs, filter_value):
    attributes = Attribute.objects.prefetch_related('values')
    merged_attributes = MergedAttributes(attributes)

    # Convert attribute:value pairs into a list of query
    queries = []
    for attr_slug, value_slug in filter_value:
        query = merged_attributes.get_query(attr_slug, value_slug)
        queries.append(query)

    # Combine full query with AND operator.
    query = functools.reduce(operator.and_, queries)
    return qs.filter(query).distinct()


def filter_products_by_price(qs, price_lte=None, price_gte=None):
    if price_lte:
        qs = qs.filter(price__lte=price_lte)
    if price_gte:
        qs = qs.filter(price__gte=price_gte)
    return qs


def filter_products_by_categories(qs, categories):
    categories = [
        category.get_descendants(include_self=True) for category in categories]
    ids = {category.id for tree in categories for category in tree}
    return qs.filter(category__in=ids)


def filter_products_by_collections(qs, collections):
    return qs.filter(collections__in=collections)


def sort_qs(qs, sort_by_product_order):
    if sort_by_product_order:
        qs = qs.order_by(sort_by_product_order['direction']
                         + sort_by_product_order['field'])
    return qs
