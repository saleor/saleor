from __future__ import unicode_literals

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
    return [hit.meta.id for hit in search.scan()]


def search(phrase, qs):
        found_objs = _execute_es_search(get_search_query(phrase))
        return qs.filter(pk__in=found_objs)
