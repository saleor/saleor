from __future__ import unicode_literals

from . import newelastic
import pytest


PHRASE = 'How fortunate man with none'
FIELDS = ['name', 'description']
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
        body=QUERY, doc_type=[DOC_TYPE], index=[INDEX])
