from unittest.mock import MagicMock, call, patch

import graphene
import pytest
from django.test import override_settings
from opentelemetry.semconv._incubating.attributes import graphql_attributes
from opentelemetry.semconv.attributes import error_attributes

from ...core.telemetry import Unit, saleor_attributes
from ...graphql.api import backend, schema
from ..metrics import (
    METRIC_GRAPHQL_QUERY_COST,
    METRIC_GRAPHQL_QUERY_COUNT,
    METRIC_GRAPHQL_QUERY_DURATION,
    METRIC_REQUEST_COUNT,
    METRIC_REQUEST_DURATION,
    record_graphql_query_count,
    record_graphql_query_duration,
)
from ..views import GraphQLView


@patch("saleor.graphql.metrics.meter")
def test_record_graphql_query_count(mock_meter):
    # when
    record_graphql_query_count(
        operation_name="name", operation_type="query", operation_identifier="identifier"
    )

    # then
    mock_meter.record.assert_any_call(
        METRIC_GRAPHQL_QUERY_COUNT,
        1,
        Unit.REQUEST,
        attributes={
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
        graphql_attributes.GRAPHQL_OPERATION_TYPE: "",
        saleor_attributes.GRAPHQL_OPERATION_IDENTIFIER: "",
    }
    mock_meter.record_duration.assert_any_call(
        METRIC_GRAPHQL_QUERY_DURATION, attributes=call_attributes
    )
    assert result == mock_context_manager


@patch("saleor.graphql.metrics.meter")
def test_graphql_query_record_metrics(mock_meter, rf, channel_USD, product_list):
    # given
    request = rf.post(
        path="/graphql/",
        data={
            "query": "query productsQuery($channel: String!) { products(first: 5, channel: $channel) { edges { node { name } } } }",
            "operationName": "productsQuery",
            "variables": {"channel": channel_USD.slug},
        },
        content_type="application/json",
    )

    # when
    view = GraphQLView.as_view(backend=backend, schema=schema)
    view(request)

    # then
    # check that saleor.graphql.operation.count is recorded
    mock_meter.record.assert_any_call(
        METRIC_GRAPHQL_QUERY_COUNT,
        1,
        Unit.REQUEST,
        attributes={
            saleor_attributes.GRAPHQL_OPERATION_IDENTIFIER: "products",
            graphql_attributes.GRAPHQL_OPERATION_TYPE: "query",
        },
    )

    # check that saleor.graphql.operation.cost is recorded
    mock_meter.record.assert_any_call(
        METRIC_GRAPHQL_QUERY_COST,
        5,
        Unit.COST,
        attributes={
            saleor_attributes.GRAPHQL_OPERATION_IDENTIFIER: "products",
            graphql_attributes.GRAPHQL_OPERATION_TYPE: "query",
        },
    )

    # check that saleor.graphql.operation.duration is recorded and has correct attributes
    mock_meter.record_duration.assert_any_call(
        METRIC_GRAPHQL_QUERY_DURATION,
        attributes={
            saleor_attributes.GRAPHQL_OPERATION_IDENTIFIER: "",
            graphql_attributes.GRAPHQL_OPERATION_TYPE: "",
        },
    )
    set_attr_calls = mock_meter.record_duration().__enter__().__setitem__.call_args_list
    assert call("graphql.operation.identifier", "products") in set_attr_calls
    assert call("graphql.operation.type", "query") in set_attr_calls


@pytest.mark.parametrize(
    ("data", "error_type", "operation_name", "operation_type", "operation_identifier"),
    [
        ("", "GraphQLError", "", "", ""),
        (
            {"query": "{"},
            "GraphQLSyntaxError",
            "",
            "",
            "",
        ),
        (
            {
                "query": "query { ... { __schema { __typename } } ... { shop { name } } }"
            },
            "GraphQLError",
            "",
            "",
            "",
        ),
        (
            {"query": "{ products(first: 9999999999) { edges { node { id } } } }"},
            "GraphQLError",
            "",
            "query",
            "products",
        ),
    ],
)
@patch("saleor.graphql.metrics.meter")
def test_graphql_query_record_metrics_invalid_query(
    mock_meter,
    data,
    error_type,
    operation_name,
    operation_type,
    operation_identifier,
    rf,
):
    # given
    request = rf.post(
        path="/graphql/",
        data=data,
        content_type="application/json",
    )

    # when
    view = GraphQLView.as_view(backend=backend, schema=schema)
    view(request)

    # then
    mock_meter.record.assert_any_call(
        METRIC_GRAPHQL_QUERY_COUNT,
        1,
        Unit.REQUEST,
        attributes={
            saleor_attributes.GRAPHQL_OPERATION_IDENTIFIER: operation_identifier,
            graphql_attributes.GRAPHQL_OPERATION_TYPE: operation_type,
            error_attributes.ERROR_TYPE: error_type,
        },
    )

    mock_meter.record.assert_any_call(
        METRIC_GRAPHQL_QUERY_COST,
        1,
        Unit.COST,
        attributes={
            saleor_attributes.GRAPHQL_OPERATION_IDENTIFIER: operation_identifier,
            graphql_attributes.GRAPHQL_OPERATION_TYPE: operation_type,
            error_attributes.ERROR_TYPE: error_type,
        },
    )

    mock_meter.record_duration.assert_any_call(
        METRIC_GRAPHQL_QUERY_DURATION,
        attributes={
            saleor_attributes.GRAPHQL_OPERATION_IDENTIFIER: "",
            graphql_attributes.GRAPHQL_OPERATION_TYPE: "",
        },
    )
    assert (
        call(error_attributes.ERROR_TYPE, error_type)
        in mock_meter.record_duration().__enter__().__setitem__.call_args_list
    )
    if operation_type:
        assert (
            call(graphql_attributes.GRAPHQL_OPERATION_TYPE, operation_type)
            in mock_meter.record_duration().__enter__().__setitem__.call_args_list
        )
    if operation_identifier:
        assert (
            call(saleor_attributes.GRAPHQL_OPERATION_IDENTIFIER, operation_identifier)
            in mock_meter.record_duration().__enter__().__setitem__.call_args_list
        )


@override_settings(GRAPHQL_QUERY_MAX_COMPLEXITY=1)
@patch("saleor.graphql.metrics.meter")
def test_graphql_query_record_metrics_cost_exceeded(
    mock_meter,
    api_client,
    variant_with_many_stocks,
    channel_USD,
):
    # given
    query_fields = "\n".join(
        [
            f"p{i}:  productVariant(id: $id, channel: $channel) {{ id }}"
            for i in range(20)
        ]
    )
    query = f"""
        query variantAvailability($id: ID!, $channel: String) {{
            {query_fields}
        }}
    """

    variables = {
        "id": graphene.Node.to_global_id("ProductVariant", variant_with_many_stocks.pk),
        "channel": channel_USD.slug,
    }

    # when
    api_client.post_graphql(query, variables)

    # then
    # check that saleor.graphql.operation.count is recorded
    mock_meter.record.assert_any_call(
        METRIC_GRAPHQL_QUERY_COUNT,
        1,
        Unit.REQUEST,
        attributes={
            saleor_attributes.GRAPHQL_OPERATION_IDENTIFIER: "productVariant",
            graphql_attributes.GRAPHQL_OPERATION_TYPE: "query",
            error_attributes.ERROR_TYPE: "QueryCostError",
        },
    )

    mock_meter.record.assert_any_call(
        METRIC_GRAPHQL_QUERY_COST,
        20,
        Unit.COST,
        attributes={
            saleor_attributes.GRAPHQL_OPERATION_IDENTIFIER: "productVariant",
            graphql_attributes.GRAPHQL_OPERATION_TYPE: "query",
            error_attributes.ERROR_TYPE: "QueryCostError",
        },
    )

    # check that saleor.graphql.operation.duration is recorded and has correct attributes
    mock_meter.record_duration.assert_any_call(
        METRIC_GRAPHQL_QUERY_DURATION,
        attributes={
            saleor_attributes.GRAPHQL_OPERATION_IDENTIFIER: "",
            graphql_attributes.GRAPHQL_OPERATION_TYPE: "",
        },
    )
    assert (
        call(error_attributes.ERROR_TYPE, "QueryCostError")
        in mock_meter.record_duration().__enter__().__setitem__.call_args_list
    )
    assert (
        call(graphql_attributes.GRAPHQL_OPERATION_TYPE, "query")
        in mock_meter.record_duration().__enter__().__setitem__.call_args_list
    )
    assert (
        call(saleor_attributes.GRAPHQL_OPERATION_IDENTIFIER, "productVariant")
        in mock_meter.record_duration().__enter__().__setitem__.call_args_list
    )


@patch("saleor.graphql.metrics.meter")
def test_graphql_view_record_http_metrics(mock_meter, rf, channel_USD, product_list):
    # given
    request = rf.post(
        path="/graphql/",
        data={
            "query": "query productsQuery($channel: String!) { products(first: 5, channel: $channel) { edges { node { name } } } }",
            "operationName": "productsQuery",
            "variables": {"channel": channel_USD.slug},
        },
        content_type="application/json",
    )

    # when
    view = GraphQLView.as_view(backend=backend, schema=schema)
    view(request)

    # then
    # check that saleor.request.count is recorded
    mock_meter.record.assert_any_call(
        METRIC_REQUEST_COUNT,
        1,
        Unit.REQUEST,
        attributes={},
    )

    # check that saleor.request.duration is recorded
    mock_meter.record_duration.assert_any_call(
        METRIC_REQUEST_DURATION,
        attributes={},
    )


@patch("saleor.graphql.metrics.meter")
@patch("saleor.graphql.views.GraphQLView._handle_query")
def test_graphql_view_record_http_metrics_error_type(mock_handle_query, mock_meter, rf):
    # given
    mock_handle_query.return_value = MagicMock(status_code=500)
    request = rf.post(
        path="/graphql/",
        data={
            "query": "query { shop { name } }",
        },
        content_type="application/json",
    )

    # when
    view = GraphQLView.as_view(backend=backend, schema=schema)
    view(request)

    # then
    # check that saleor.request.count is recorded
    mock_meter.record.assert_any_call(
        METRIC_REQUEST_COUNT,
        1,
        Unit.REQUEST,
        attributes={error_attributes.ERROR_TYPE: "500"},
    )

    # check that saleor.request.duration is recorded
    mock_meter.record_duration.assert_any_call(
        METRIC_REQUEST_DURATION,
        attributes={},
    )
    assert (
        call(error_attributes.ERROR_TYPE, "500")
        in mock_meter.record_duration().__enter__().__setitem__.call_args_list
    )
