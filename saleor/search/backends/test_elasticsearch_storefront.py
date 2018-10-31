from . import elasticsearch_storefront

PHRASE = 'How fortunate man with none'
FIELDS = ['title', 'name', 'description']
INDEX = 'storefront'
DOC_TYPE = 'doc'
QUERY = {
    '_source': False,
    'query': {
        'bool': {
            'must': [{
                'multi_match': {
                    'query': PHRASE,
                    'fields': FIELDS}}],
            'filter': [{
                'term': {
                    'is_published': True}}]}}}


def test_storefront_product_search_query_syntax():
    assert QUERY == elasticsearch_storefront.get_search_query(PHRASE).to_dict()
