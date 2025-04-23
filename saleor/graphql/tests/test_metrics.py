from unittest.mock import patch

from opentelemetry.semconv._incubating.attributes import graphql_attributes

from ...core.telemetry import Unit, saleor_attributes
from ..metrics import (
    METRIC_GRAPHQL_QUERY_COUNT,
    METRIC_GRAPHQL_QUERY_DURATION,
    record_graphql_query_count,
    record_graphql_query_duration,
)


@patch("saleor.graphql.metrics.meter")
def test_record_graphql_query_count(mock_meter):
    # when
    record_graphql_query_count(
        operation_name="name", operation_type="query", operation_identifier="identifier"
    )

    # then
    mock_meter.record.assert_called_once_with(
        METRIC_GRAPHQL_QUERY_COUNT,
        1,
        Unit.REQUEST,
        attributes={
            graphql_attributes.GRAPHQL_OPERATION_NAME: "name",
            graphql_attributes.GRAPHQL_OPERATION_TYPE: "query",
            saleor_attributes.GRAPHQL_OPERATION_IDENTIFIER: "identifier",
        },
    )


@patch("saleor.graphql.metrics.meter")
def test_record_graphql_query_duration(mock_meter):
    # given
    mock_context_manager = object()
    mock_meter.record_duration.return_value = mock_context_manager

    # when
    result = record_graphql_query_duration()

    # then
    call_attributes = {
        graphql_attributes.GRAPHQL_OPERATION_NAME: "",
        graphql_attributes.GRAPHQL_OPERATION_TYPE: "",
        saleor_attributes.GRAPHQL_OPERATION_IDENTIFIER: "",
    }
    mock_meter.record_duration.assert_called_once_with(
        METRIC_GRAPHQL_QUERY_DURATION, attributes=call_attributes
    )
    assert result == mock_context_manager
