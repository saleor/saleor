import functools
import operator
from collections import defaultdict

from django.db.models import Q

from ...product.models import Attribute


def filter_products_by_attributes(qs, filter_value):
    attributes = Attribute.objects.prefetch_related('values')
    attributes_map = {
        attribute.slug: attribute.pk for attribute in attributes}
    values_map = {
        attr.slug: {value.slug: value.pk for value in attr.values.all()}
        for attr in attributes}
    queries = defaultdict(list)
    # Convert attribute:value pairs into a dictionary where
    # attributes are keys and values are grouped in lists
    for attr_name, val_slug in filter_value:
        if attr_name not in attributes_map:
            raise ValueError('Unknown attribute name: %r' % (attr_name, ))
        attr_pk = attributes_map[attr_name]
        attr_val_pk = values_map[attr_name].get(val_slug, val_slug)
        queries[attr_pk].append(attr_val_pk)
    # Combine filters of the same attribute with OR operator
    # and then combine full query with AND operator.
    combine_and = [
        functools.reduce(
            operator.or_, [
                Q(**{'variants__attributes__%s' % (key, ): v}) |
                Q(**{'attributes__%s' % (key, ): v}) for v in values])
        for key, values in queries.items()]
    query = functools.reduce(operator.and_, combine_and)
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
    ids = set([category.id for tree in categories for category in tree])
    return qs.filter(category__in=ids)


def filter_products_by_collections(qs, collections):
    return qs.filter(collections__in=collections)


def sort_qs(qs, sort_by):
    if sort_by:
        qs = qs.order_by(sort_by)
    return qs
