from elasticsearch_dsl.query import MultiMatch

from ..documents import ProductDocument


def get_search_query(phrase):
    ''' Execute external search for product matching phrase  '''
    query = MultiMatch(fields=['title', 'name', 'description'], query=phrase)
    return (ProductDocument.search()
                           .query(query)
                           .source(False)
                           .filter('term', is_published=True))


def search(phrase):
    return get_search_query(phrase).to_queryset()
