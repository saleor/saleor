from . import newelastic
import pytest


@pytest.fixture
def search_phrase():
    return 'How fortunate man with none'


@pytest.fixture
def es_search_query(search_phrase):
    query = {
        '_source': ['pk'],
        'query': {
            'multi_match': {
                'fields': ['name', 'description'],
                'query': 'How fortunate man with none'
            }
        }
    }
    return query


def test_no_result_search(mocker, es_search_query, search_phrase):
    mocker.patch.object(newelastic.CLIENT, 'search', returnvalue=[])
    products = newelastic.search(search_phrase)
    newelastic.CLIENT.search.assert_called_once_with(
        body=es_search_query, doc_type=[], index=None)
    assert not products
