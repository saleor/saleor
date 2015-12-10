from __future__ import unicode_literals

from selectable.base import LookupBase
from selectable.registry import registry
from django.db.models import Count

from .models import Product


class CollectionLookup(LookupBase):
    def get_query(self, request, term):
        products = Product.objects.filter(collection__isnull=False,
                                          collection__istartswith=term)
        products = products.select_subclasses()
        qs = products.values('collection').annotate(
            products=Count('collection')).order_by('-products')
        return qs

    def get_item_value(self, item):
        return item['collection']

    def get_item_label(self, item):
        collections = '{collection} ({products} products)'.format(**item)
        return collections


registry.register(CollectionLookup)
