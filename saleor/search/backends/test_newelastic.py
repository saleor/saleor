from . import newelastic


def test_search(mocker):
    mocker.patch.object(newelastic.CLIENT, 'search', returnvalue=[])
    phrase = 'foo'
    products = newelastic.search(phrase)
    expected_query = {
        'query': {
            'multi_match': {
                'fields': ['name', 'description'],
                'query': phrase
            }
        }
    }
    newelastic.CLIENT.search.assert_called_once_with(
        body=expected_query, doc_type=[], index=None)
    assert not products
