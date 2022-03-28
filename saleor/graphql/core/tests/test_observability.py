from unittest.mock import Mock, patch

EXAMPLE_QUERY = "{ shop { name } }"


@patch("saleor.graphql.views.observability_reporter.ApiCallResponse")
def test_observability_report_api_call_with_report_all_api_calls(
    mock_api_call_response_class, api_client
):
    query_shop = "{ shop { name } }"
    mock_api_call = Mock()
    mock_api_call_response_class.return_value = mock_api_call

    api_client.post_graphql(query_shop, variables={})

    assert mock_api_call.report.call_count >= 1
