from __future__ import unicode_literals

from . import newelastic
import pytest


PHRASE = 'How fortunate man with none'
CONTENT_TYPE = 'product.Product'
FIELDS = ['name', 'description']
INDEX = 'storefront__product_product'
QUERY = {
        'query': {
            'bool': {
                'must': [{
                    'multi_match': {
                        'fields': FIELDS,
                        'query': 'How fortunate man with none'
                    }
                }],
                'filter': [{
                    'term': {
                        'is_published_filter': True
                    }
                }, {
                    'match': {
                        'content_type': CONTENT_TYPE
                    }
                }]
            }
        },
        '_source': ['pk']
    }


@pytest.fixture
def elasticsearch_client(mocker):
    SETTINGS = {'URLS': ['http://localhost']}
    nes = newelastic.SearchBackend(SETTINGS)
    mocker.patch.object(
        newelastic.SearchBackend.client, 'search', returnvalue=[])
    return nes


def test_storefront_product_search_query_syntax(elasticsearch_client):
    products = newelastic.search_products(PHRASE)
    newelastic.SearchBackend.client.search.assert_called_once_with(
        body=QUERY, doc_type=[], index=[INDEX])
    assert not products
