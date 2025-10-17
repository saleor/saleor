from unittest.mock import MagicMock, patch

import graphene
import pytest
from django.test import override_settings
from freezegun import freeze_time
from opentelemetry.semconv._incubating.attributes import graphql_attributes

from ...core.telemetry import DEFAULT_DURATION_BUCKETS, Scope, Unit, saleor_attributes
from ...graphql.api import backend, schema
from ...tests.utils import get_metric_and_data_point, get_metric_data
from ..metrics import (
    METRIC_GRAPHQL_QUERY_COST,
    METRIC_GRAPHQL_QUERY_COUNT,
    METRIC_GRAPHQL_QUERY_DURATION,
    METRIC_GRAPHQL_SLOW_OPERATION_DURATION,
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
    assert data_point.attributes == {"graphql.operation.type": "query"}
    assert data_point.value == 1


def test_record_graphql_query_duration(get_test_metrics_data, settings):
    # given
    settings.TELEMETRY_SLOW_GRAPHQL_OPERATION_THRESHOLD = 1.0
    operation_duration = 0.25
    fingerprint = "query:productsQuery:4aace3b174967edf8ed6e6c894d26f9d"
    # when
    with freeze_time("2025-10-13 12:00:00") as frozen_datetime:
        with record_graphql_query_duration() as query_duration_attrs:
            query_duration_attrs[graphql_attributes.GRAPHQL_OPERATION_TYPE] = "query"
            query_duration_attrs[saleor_attributes.GRAPHQL_DOCUMENT_FINGERPRINT] = (
                fingerprint
            )
            frozen_datetime.tick(delta=operation_duration)

    # then
    metrics_data = get_test_metrics_data()
    metric_data, data_point = get_metric_and_data_point(
        metrics_data, METRIC_GRAPHQL_QUERY_DURATION
    )
    assert metric_data.unit == Unit.SECOND.value
    assert data_point.attributes == {"graphql.operation.type": "query"}
    assert data_point.explicit_bounds == tuple(DEFAULT_DURATION_BUCKETS)
    assert data_point.count == 1
    assert data_point.sum == operation_duration

    assert get_metric_data(metrics_data, METRIC_GRAPHQL_SLOW_OPERATION_DURATION) is None


def test_record_graphql_query_duration_with_slow_query(get_test_metrics_data, settings):
    # given
    settings.TELEMETRY_SLOW_GRAPHQL_OPERATION_THRESHOLD = operation_duration = 1.0
    fingerprint = "query:productsQuery:4aace3b174967edf8ed6e6c894d26f9d"
    # when
    with freeze_time("2025-10-13 12:00:00") as frozen_datetime:
        with record_graphql_query_duration() as query_duration_attrs:
            query_duration_attrs[graphql_attributes.GRAPHQL_OPERATION_TYPE] = "query"
            query_duration_attrs[saleor_attributes.GRAPHQL_DOCUMENT_FINGERPRINT] = (
                fingerprint
            )
            frozen_datetime.tick(delta=operation_duration)

    # then
    metrics_data = get_test_metrics_data()
    duration_metric, duration_data_point = get_metric_and_data_point(
        metrics_data, METRIC_GRAPHQL_QUERY_DURATION
    )
    assert duration_metric.unit == Unit.SECOND.value
    assert duration_data_point.attributes == {"graphql.operation.type": "query"}
    assert duration_data_point.explicit_bounds == tuple(DEFAULT_DURATION_BUCKETS)
    assert duration_data_point.count == 1
    assert duration_data_point.sum == operation_duration

    slow_operation_metric, slow_operation_data_point = get_metric_and_data_point(
        metrics_data, METRIC_GRAPHQL_SLOW_OPERATION_DURATION, scope=Scope.CORE
    )
    assert slow_operation_metric.unit == Unit.SECOND.value
    assert slow_operation_data_point.attributes == {
        "graphql.operation.type": "query",
        "graphql.document_fingerprint": fingerprint,
    }
    assert slow_operation_data_point.explicit_bounds == tuple(DEFAULT_DURATION_BUCKETS)
    assert slow_operation_data_point.count == 1
    assert slow_operation_data_point.sum == operation_duration


def test_graphql_query_record_metrics(
    get_test_metrics_data, rf, channel_USD, product_list, settings
):
    # given
    settings.TELEMETRY_SLOW_GRAPHQL_OPERATION_THRESHOLD = 0.0
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
    metrics_data = get_test_metrics_data()
    count_metric, count_data_point = get_metric_and_data_point(
        metrics_data, METRIC_GRAPHQL_QUERY_COUNT
    )
    assert count_metric.unit == Unit.REQUEST.value
    assert count_data_point.attributes == {"graphql.operation.type": "query"}
    assert count_data_point.value == 1

    # check that saleor.graphql.operation.cost is recorded
    cost_metric, cost_data_point = get_metric_and_data_point(
        metrics_data, METRIC_GRAPHQL_QUERY_COST
    )
    assert cost_metric.unit == Unit.COST.value
    assert cost_data_point.attributes == {"graphql.operation.type": "query"}
    assert cost_data_point.explicit_bounds == tuple(QUERY_COST_BUCKETS)
    assert cost_data_point.count == 1
    assert cost_data_point.sum == 5

    # check that saleor.graphql.operation.duration is recorded and has correct attributes
    duration_metric, duration_data_point = get_metric_and_data_point(
        metrics_data, METRIC_GRAPHQL_QUERY_DURATION
    )
    assert duration_metric.unit == Unit.SECOND.value
    assert duration_data_point.attributes == {"graphql.operation.type": "query"}
    assert duration_data_point.count == 1

    # check that saleor.graphql.slow_operation.duration is recorded and has correct attributes
    slow_operation_metric, slow_operation_data_point = get_metric_and_data_point(
        metrics_data, METRIC_GRAPHQL_SLOW_OPERATION_DURATION, scope=Scope.CORE
    )
    assert slow_operation_metric.unit == Unit.SECOND.value
    assert slow_operation_data_point.attributes == {
        "graphql.operation.type": "query",
        "graphql.document_fingerprint": "query:productsQuery:4aace3b174967edf8ed6e6c894d26f9d",
    }
    assert slow_operation_data_point.count == 1


@pytest.mark.parametrize(
    ("data", "error_type", "operation_type", "slow_operation_attributes"),
    [
        ("", "GraphQLError", "", {}),
        ({"query": "{"}, "GraphQLSyntaxError", "", {}),
        (
            {
                "query": "query { ... { __schema { __typename } } ... { shop { name } } }"
            },
            "GraphQLError",
            "",
            {},
        ),
        (
            {"query": "{ products(first: 9999999999) { edges { node { id } } } }"},
            "GraphQLError",
            "query",
            {"graphql.document_fingerprint": "query:22f6cfd4453eeba3e758ccda9f6b0e93"},
        ),
    ],
)
def test_graphql_query_record_metrics_invalid_query(
    get_test_metrics_data,
    data,
    error_type,
    operation_type,
    slow_operation_attributes,
    rf,
    settings,
):
    # given
    settings.TELEMETRY_SLOW_GRAPHQL_OPERATION_THRESHOLD = 0.0
    request = rf.post(
        path="/graphql/",
        data=data,
        content_type="application/json",
    )
    attributes = {
        "graphql.operation.type": operation_type,
        "error.type": error_type,
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
    assert duration_data_point.count == 1

    slow_operation_metric, slow_operation_data_point = get_metric_and_data_point(
        metrics_data, METRIC_GRAPHQL_SLOW_OPERATION_DURATION, scope=Scope.CORE
    )
    assert slow_operation_metric.unit == Unit.SECOND.value
    assert slow_operation_data_point.attributes == {
        **attributes,
        **slow_operation_attributes,
    }
    assert slow_operation_data_point.count == 1


@override_settings(GRAPHQL_QUERY_MAX_COMPLEXITY=1)
def test_graphql_query_record_metrics_cost_exceeded(
    get_test_metrics_data,
    api_client,
    variant_with_many_stocks,
    channel_USD,
    settings,
):
    # given
    settings.TELEMETRY_SLOW_GRAPHQL_OPERATION_THRESHOLD = 0.0
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
        "graphql.operation.type": "query",
        "error.type": "QueryCostError",
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
    assert duration_data_point.count == 1

    slow_operation_metric, slow_operation_data_point = get_metric_and_data_point(
        metrics_data, METRIC_GRAPHQL_SLOW_OPERATION_DURATION, scope=Scope.CORE
    )
    assert slow_operation_metric.unit == Unit.SECOND.value
    assert slow_operation_data_point.attributes == {
        **attributes,
        "graphql.document_fingerprint": "query:variantAvailability:ddeb5d8f061864b4b3ab75418e225cc1",
    }
    assert slow_operation_data_point.count == 1


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
    assert count_data_point.attributes == {"error.type": "500"}
    assert count_data_point.value == 1

    # check that saleor.request.duration is recorded
    duration_metric, duration_data_point = get_metric_and_data_point(
        metrics_data, METRIC_REQUEST_DURATION
    )
    assert duration_metric.unit == Unit.SECOND.value
    assert duration_data_point.attributes == {"error.type": "500"}
    assert duration_data_point.count == 1
