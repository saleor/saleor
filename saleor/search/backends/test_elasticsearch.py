from __future__ import unicode_literals
from . import elasticsearch

PHRASE = 'How fortunate man with none'
FIELDS = ['title', 'name', 'description']
INDEX = 'storefront'
DOC_TYPE = 'product_document'
QUERY = {
    '_source': False,
    'query': {
        'bool': {
            'must': [{
                'multi_match': {
                    'query': PHRASE,
                    'fields': FIELDS
                }
            }],
            'filter': [{
                'term': {
                    'is_published': True
                }
            }]
        }
    }
}


def test_storefront_product_search_query_syntax():
    assert QUERY == elasticsearch.get_search_query(PHRASE).to_dict()
