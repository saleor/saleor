from . import elasticsearch_dashboard

PHRASE = 'You can go to the west'
PRODUCT_QUERY = {
    '_source': False,
    'query': {
        'multi_match': {
            'fields': ['name', 'title', 'description'],
            'query': PHRASE,
            'type': 'cross_fields'}},
    'sort': ['_score']}
ORDERS_QUERY = {
    '_source': False,
    'query': {
        'multi_match': {
            'fields': ['user', 'first_name', 'last_name', 'discount_name'],
            'query': PHRASE}}}
USERS_QUERY = {
    '_source': False,
    'query': {
        'multi_match': {
            'fields': ['user', 'email', 'first_name', 'last_name'],
            'operator': 'and',
            'query': PHRASE,
            'type': 'cross_fields'}}}


def test_dashboard_search_query_syntax():
    ''' Check if generated ES queries have desired syntax '''
    searches = elasticsearch_dashboard.get_search_queries(PHRASE)
    assert PRODUCT_QUERY == searches['products'].to_dict()
    assert ORDERS_QUERY == searches['orders'].to_dict()
    assert USERS_QUERY == searches['users'].to_dict()
