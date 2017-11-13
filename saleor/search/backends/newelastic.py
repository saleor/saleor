from __future__ import unicode_literals

from django.db.models.query import QuerySet
from elasticsearch_dsl.query import MultiMatch
from ..documents import ProductDocument


def search_products(phrase):
    ''' Execute external search for product matching phrase  '''
    query = MultiMatch(fields=['name', 'description'], query=phrase)
    search = (ProductDocument.search()
                             .query(query)
                             .source(False)
                             .filter('term', is_published=True))
    return [hit.meta.id for hit in search.execute()]


def search(query, model_or_queryset):
        qs = model_or_queryset
        # TODO: remove this ugly type incoherence of old search api
        if not isinstance(model_or_queryset, QuerySet):
            qs = model_or_queryset.objects.all()
        return qs.filter(pk__in=search_products(query))



