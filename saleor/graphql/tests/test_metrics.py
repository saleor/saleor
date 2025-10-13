from unittest.mock import MagicMock, patch

import graphene
import pytest
from django.test import override_settings
from opentelemetry.semconv._incubating.attributes import graphql_attributes
from opentelemetry.semconv.attributes import error_attributes

from ...core.telemetry import DEFAULT_DURATION_BUCKETS, Unit
from ...graphql.api import backend, schema
from ...tests.utils import get_metric_and_data_point
from ..metrics import (
    METRIC_GRAPHQL_QUERY_COST,
    METRIC_GRAPHQL_QUERY_COUNT,
    METRIC_GRAPHQL_QUERY_DURATION,
    METRIC_REQUEST_COUNT,
    METRIC_REQUEST_DURATION,
    QUERY_COST_BUCKETS,
    record_graphql_query_count,
    record_graphql_query_duration,
)
from ..views import GraphQLView


def test_record_graphql_query_count(get_test_metrics_data):
    # when
    record_graphql_query_count(operation_type="query")
    # then
    metric_data, data_point = get_metric_and_data_point(
        get_test_metrics_data(), METRIC_GRAPHQL_QUERY_COUNT
    )
    assert metric_data.unit == Unit.REQUEST.value
    assert data_point.attributes == {graphql_attributes.GRAPHQL_OPERATION_TYPE: "query"}
    assert data_point.value == 1


def test_record_graphql_query_duration(get_test_metrics_data):
    # when
    with record_graphql_query_duration() as query_duration_attrs:
        query_duration_attrs[graphql_attributes.GRAPHQL_OPERATION_TYPE] = "query"

    # then
    metric_data, data_point = get_metric_and_data_point(
        get_test_metrics_data(), METRIC_GRAPHQL_QUERY_DURATION
    )
    assert metric_data.unit == Unit.SECOND.value
    assert data_point.attributes == {graphql_attributes.GRAPHQL_OPERATION_TYPE: "query"}
    assert data_point.explicit_bounds == tuple(DEFAULT_DURATION_BUCKETS)
    assert data_point.count == 1


def test_graphql_query_record_metrics(
    get_test_metrics_data, rf, channel_USD, product_list
):
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
    attributes = {graphql_attributes.GRAPHQL_OPERATION_TYPE: "query"}

    # when
    view = GraphQLView.as_view(backend=backend, schema=schema)
    view(request)

    # then
    # check that saleor.graphql.operation.count is recorded
    metrics_data = get_test_metrics_data()
    count_metric, count_data_point = get_metric_and_data_point(
        metrics_data, METRIC_GRAPHQL_QUERY_COUNT
    )
    assert count_metric.unit == Unit.REQUEST.value
    assert count_data_point.attributes == attributes
    assert count_data_point.value == 1

    # check that saleor.graphql.operation.cost is recorded
    cost_metric, cost_data_point = get_metric_and_data_point(
        metrics_data, METRIC_GRAPHQL_QUERY_COST
    )
    assert cost_metric.unit == Unit.COST.value
    assert cost_data_point.attributes == attributes
    assert cost_data_point.explicit_bounds == tuple(QUERY_COST_BUCKETS)
    assert cost_data_point.count == 1
    assert cost_data_point.sum == 5

    # check that saleor.graphql.operation.duration is recorded and has correct attributes
    duration_metric, duration_data_point = get_metric_and_data_point(
        metrics_data, METRIC_GRAPHQL_QUERY_DURATION
    )
    assert duration_metric.unit == Unit.SECOND.value
    assert duration_data_point.attributes == attributes
    assert duration_data_point.explicit_bounds == tuple(DEFAULT_DURATION_BUCKETS)
    assert duration_data_point.count == 1


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
def test_graphql_query_record_metrics_invalid_query(
    get_test_metrics_data,
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
    attributes = {
        graphql_attributes.GRAPHQL_OPERATION_TYPE: operation_type,
        error_attributes.ERROR_TYPE: error_type,
    }

    # when
    view = GraphQLView.as_view(backend=backend, schema=schema)
    view(request)

    # then
    metrics_data = get_test_metrics_data()
    count_metric, count_data_point = get_metric_and_data_point(
        metrics_data, METRIC_GRAPHQL_QUERY_COUNT
    )
    assert count_metric.unit == Unit.REQUEST.value
    assert count_data_point.attributes == attributes
    assert count_data_point.value == 1

    cost_metric, cost_data_point = get_metric_and_data_point(
        metrics_data, METRIC_GRAPHQL_QUERY_COST
    )
    assert cost_metric.unit == Unit.COST.value
    assert cost_data_point.attributes == attributes
    assert cost_data_point.explicit_bounds == tuple(QUERY_COST_BUCKETS)
    assert cost_data_point.count == 1
    assert cost_data_point.sum == 1

    duration_metric, duration_data_point = get_metric_and_data_point(
        metrics_data, METRIC_GRAPHQL_QUERY_DURATION
    )
    assert duration_metric.unit == Unit.SECOND.value
    assert duration_data_point.attributes == attributes
    assert duration_data_point.explicit_bounds == tuple(DEFAULT_DURATION_BUCKETS)
    assert duration_data_point.count == 1


@override_settings(GRAPHQL_QUERY_MAX_COMPLEXITY=1)
def test_graphql_query_record_metrics_cost_exceeded(
    get_test_metrics_data,
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

    attributes = {
        graphql_attributes.GRAPHQL_OPERATION_TYPE: "query",
        error_attributes.ERROR_TYPE: "QueryCostError",
    }

    # when
    api_client.post_graphql(query, variables)

    # then
    metrics_data = get_test_metrics_data()
    # check that saleor.graphql.operation.count is recorded
    count_metric, count_data_point = get_metric_and_data_point(
        metrics_data, METRIC_GRAPHQL_QUERY_COUNT
    )
    assert count_metric.unit == Unit.REQUEST.value
    assert count_data_point.attributes == attributes
    assert count_data_point.value == 1

    cost_metric, cost_data_point = get_metric_and_data_point(
        metrics_data, METRIC_GRAPHQL_QUERY_COST
    )
    assert cost_metric.unit == Unit.COST.value
    assert cost_data_point.attributes == attributes
    assert cost_data_point.explicit_bounds == tuple(QUERY_COST_BUCKETS)
    assert cost_data_point.count == 1
    assert cost_data_point.sum == 20

    # check that saleor.graphql.operation.duration is recorded and has correct attributes
    duration_metric, duration_data_point = get_metric_and_data_point(
        metrics_data, METRIC_GRAPHQL_QUERY_DURATION
    )
    assert duration_metric.unit == Unit.SECOND.value
    assert duration_data_point.attributes == attributes
    assert duration_data_point.explicit_bounds == tuple(DEFAULT_DURATION_BUCKETS)
    assert duration_data_point.count == 1


def test_graphql_view_record_http_metrics(
    get_test_metrics_data, rf, channel_USD, product_list
):
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
    metrics_data = get_test_metrics_data()
    # check that saleor.request.count is recorded
    count_metric, count_data_point = get_metric_and_data_point(
        metrics_data, METRIC_REQUEST_COUNT
    )
    assert count_metric.unit == Unit.REQUEST.value
    assert count_data_point.attributes == {}
    assert count_data_point.value == 1

    # check that saleor.request.duration is recorded
    duration_metric, duration_data_point = get_metric_and_data_point(
        metrics_data, METRIC_REQUEST_DURATION
    )
    assert duration_metric.unit == Unit.SECOND.value
    assert duration_data_point.attributes == {}
    assert duration_data_point.explicit_bounds == tuple(DEFAULT_DURATION_BUCKETS)
    assert duration_data_point.count == 1


@patch("saleor.graphql.views.GraphQLView._handle_query")
def test_graphql_view_record_http_metrics_error_type(
    mock_handle_query, get_test_metrics_data, rf
):
    # given
    mock_handle_query.return_value = MagicMock(status_code=500)
    request = rf.post(
        path="/graphql/",
        data={
            "query": "query { shop { name } }",
        },
        content_type="application/json",
    )
    attributes = {error_attributes.ERROR_TYPE: "500"}

    # when
    view = GraphQLView.as_view(backend=backend, schema=schema)
    view(request)

    # then
    metrics_data = get_test_metrics_data()
    # check that saleor.request.count is recorded
    count_metric, count_data_point = get_metric_and_data_point(
        metrics_data, METRIC_REQUEST_COUNT
    )
    assert count_metric.unit == Unit.REQUEST.value
    assert count_data_point.attributes == attributes
    assert count_data_point.value == 1

    # check that saleor.request.duration is recorded
    duration_metric, duration_data_point = get_metric_and_data_point(
        metrics_data, METRIC_REQUEST_DURATION
    )
    assert duration_metric.unit == Unit.SECOND.value
    assert duration_data_point.attributes == attributes
    assert duration_data_point.explicit_bounds == tuple(DEFAULT_DURATION_BUCKETS)
    assert duration_data_point.count == 1
