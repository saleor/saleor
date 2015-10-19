from .serializers import GetWebhookRequestSerializer


def test_get_webhook_serializer():
    test_since = '2015-01-01T12:15:00Z'
    payload = {
        'request_id': '52f367367575e449c3000001',
        'parameters': {
            'since': test_since
        }
    }
    serializer = GetWebhookRequestSerializer(data=payload,
                                             since_query_field='last_updated')
    assert serializer.is_valid()
    query_filter = serializer.get_query_filter()
    assert len(query_filter.children) == 1
    query = query_filter.children[0][0]
    query_value = query_filter.children[0][1]
    assert query == 'last_updated__gte'
    assert query_value == test_since
