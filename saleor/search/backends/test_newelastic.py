from __future__ import unicode_literals

from . import newelastic
import pytest


@pytest.fixture
def search_phrase():
    return 'How fortunate man with none'


@pytest.fixture
def es_search_query(search_phrase):
    CONTENT_TYPE = 'product.Product'
    FIELDS = ['name', 'description']
    return {
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
def storefront_index():
    return 'storefront__product_product'


def test_storefront_product_search_query_syntax(
        mocker, es_search_query, search_phrase, storefront_index):
    mocker.patch.object(newelastic.CLIENT, 'search', returnvalue=[])
    products = newelastic.search_products(search_phrase)
    newelastic.CLIENT.search.assert_called_once_with(
        body=es_search_query, doc_type=[], index=[storefront_index])
    assert not products
