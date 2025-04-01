from unittest.mock import patch

from ..metrics import (
    METRIC_GRAPHQL_QUERIES,
    METRIC_GRAPHQL_QUERY_DURATION,
    record_graphql_queries_count,
    record_graphql_query_duration,
)


@patch("saleor.graphql.metrics.meter")
def test_record_graphql_queries_count(mock_meter):
    # when
    record_graphql_queries_count(5)

    # then
    mock_meter.record.assert_called_once_with(METRIC_GRAPHQL_QUERIES, 5)


@patch("saleor.graphql.metrics.meter")
def test_record_graphql_query_duration(mock_meter):
    # given
    mock_context_manager = object()
    mock_meter.record_duration.return_value = mock_context_manager

    # when
    result = record_graphql_query_duration()

    # then
    mock_meter.record_duration.assert_called_once_with(METRIC_GRAPHQL_QUERY_DURATION)
    assert result == mock_context_manager
