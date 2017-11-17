from __future__ import unicode_literals

from django.db.models.query import QuerySet
from elasticsearch_dsl.query import MultiMatch
from ..documents import ProductDocument


def get_search_query(phrase):
    ''' Execute external search for product matching phrase  '''
    query = MultiMatch(fields=['title', 'name', 'description'], query=phrase)
    return (ProductDocument.search()
                           .query(query)
                           .source(False)
                           .filter('term', is_published=True))


def _execute_es_search(search):
    return [hit.meta.id for hit in search.execute()]


def search(query, model_or_queryset):
        qs = model_or_queryset
        # TODO: remove this ugly type incoherence of old search api
        if not isinstance(model_or_queryset, QuerySet):
            qs = model_or_queryset.objects.all()
        found_objs = _execute_es_search(get_search_query(query))
        return qs.filter(pk__in=found_objs)
