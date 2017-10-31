from __future__ import unicode_literals

from . import newelastic
import pytest


@pytest.fixture
def search_phrase():
    return 'How fortunate man with none'


@pytest.fixture
def es_search_query(search_phrase):
    query = {
        'query': {
            'multi_match': {
                'query': 'How fortunate man with none',
                'fields': ['name', 'description']
            }
        },
        '_source': ['pk']
    }
    return query


@pytest.fixture
def storefront_index():
    return 'storefront__product_product'


def test_no_result_search(mocker, es_search_query, search_phrase,
                          storefront_index):
    mocker.patch.object(newelastic.CLIENT, 'search', returnvalue=[])
    products = newelastic.search_products(search_phrase)
    newelastic.CLIENT.search.assert_called_once_with(
        body=es_search_query, doc_type=[], index=[storefront_index])
    assert not products
