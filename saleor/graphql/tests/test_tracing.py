import hashlib
from unittest.mock import MagicMock, patch

import graphene
import pytest
from django.test import override_settings
from opentelemetry.sdk.trace import ReadableSpan
from opentelemetry.trace import StatusCode

from ...graphql.api import backend, schema
from ..views import GraphQLView


@pytest.fixture
def get_test_spans(in_memory_span_exporter):
    # Clear any existing spans from the buffer before test execution
    in_memory_span_exporter.clear()
    yield in_memory_span_exporter.get_finished_spans
    # Clean up by clearing the buffer after test completion
    in_memory_span_exporter.clear()


def get_spans_by_name(spans, name) -> tuple[ReadableSpan, ...]:
    return tuple(span for span in spans if span.name == name)


def get_span_by_name(spans, name) -> ReadableSpan:
    filtered = get_spans_by_name(spans, name)
    assert len(filtered) == 1, f"Multiple '{name}' spans"
    return filtered[0]


def test_tracing_query_hashing(
    staff_api_client,
    permission_manage_products,
    get_test_spans,
):
    # given
    query = """
        query test {
          products(first:5) {
            edges{
              node{
                id
                name
              }
            }
          }
        }
    """
    staff_api_client.user.user_permissions.add(permission_manage_products)

    # when
    staff_api_client.post_graphql(query)
    span = get_span_by_name(get_test_spans(), "graphql_query")

    # then
    hash = hashlib.md5(span.attributes["graphql.query"].encode("utf-8")).hexdigest()
    assert span.attributes["graphql.query_fingerprint"] == f"query:test:{hash}"


def test_tracing_query_hashing_with_fragment(
    staff_api_client,
    permission_manage_products,
    get_test_spans,
):
    # given
    query = """
        fragment ProductVariant on ProductVariant {
          id
        }
        query test {
          products(first:5) {
            edges{
              node{
                id
                name
                variants {
                  ...ProductVariant
                }
              }
            }
          }
        }
    """
    staff_api_client.user.user_permissions.add(permission_manage_products)

    # when
    staff_api_client.post_graphql(query)
    span = get_span_by_name(get_test_spans(), "graphql_query")

    # then
    hash = hashlib.md5(span.attributes["graphql.query"].encode("utf-8")).hexdigest()
    assert span.attributes["graphql.query_fingerprint"] == f"query:test:{hash}"


def test_tracing_query_hashing_different_vars_same_checksum(
    staff_api_client,
    permission_manage_products,
    get_test_spans,
):
    # given
    query = """
        query test($first: Int!) {
          products(first: $first) {
            edges{
              node{
                id
                name
              }
            }
          }
        }
    """
    staff_api_client.user.user_permissions.add(permission_manage_products)
    QUERIES = 5

    # when
    for i in range(QUERIES):
        staff_api_client.post_graphql(query, {"first": i + 1})

    # then
    fingerprints = [
        span.attributes["graphql.query_fingerprint"]
        for span in get_spans_by_name(get_test_spans(), "graphql_query")
    ]
    assert len(fingerprints) == QUERIES
    assert len(set(fingerprints)) == 1


def test_tracing_query_hashing_unnamed_query(
    staff_api_client,
    permission_manage_products,
    get_test_spans,
):
    # given
    query = """
        query {
          products(first:5) {
            edges{
              node{
                id
                name
              }
            }
          }
        }
    """
    staff_api_client.user.user_permissions.add(permission_manage_products)

    # when
    staff_api_client.post_graphql(query)
    span = get_span_by_name(get_test_spans(), "graphql_query")

    # then
    hash = hashlib.md5(span.attributes["graphql.query"].encode("utf-8")).hexdigest()
    assert span.attributes["graphql.query_fingerprint"] == f"query:{hash}"


def test_tracing_query_hashing_unnamed_query_no_query_spec(
    staff_api_client,
    permission_manage_products,
    get_test_spans,
):
    # given
    query = """
        {
          products(first:5) {
            edges{
              node{
                id
                name
              }
            }
          }
        }
    """
    staff_api_client.user.user_permissions.add(permission_manage_products)

    # when
    staff_api_client.post_graphql(query)
    span = get_span_by_name(get_test_spans(), "graphql_query")

    # then
    hash = hashlib.md5(span.attributes["graphql.query"].encode("utf-8")).hexdigest()
    assert span.attributes["graphql.query_fingerprint"] == f"query:{hash}"


def test_tracing_mutation_hashing(
    staff_api_client,
    permission_manage_orders,
    order_with_lines,
    get_test_spans,
):
    # given
    order = order_with_lines
    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id}
    mutation = """
        mutation cancelOrder($id: ID!) {
            orderCancel(id: $id) {
                order {
                    status
                }
                errors{
                    field
                    code
                }
            }
        }
    """

    # when
    staff_api_client.post_graphql(
        mutation,
        variables,
        permissions=[permission_manage_orders],
        check_no_permissions=False,
    )
    span = get_span_by_name(get_test_spans(), "graphql_query")

    # then
    hash = hashlib.md5(span.attributes["graphql.query"].encode("utf-8")).hexdigest()
    assert (
        span.attributes["graphql.query_fingerprint"] == f"mutation:cancelOrder:{hash}"
    )


def test_tracing_query_identifier_for_query(
    staff_api_client,
    permission_manage_products,
    get_test_spans,
):
    # given
    query = """
        query test {
          products(first: 5, channel:"default-channel") {
            edges {
              node {
                id
              }
            }
          }
          otherProducts: products(first: 5, channel:"default-channel") {
            edges {
              node {
                id
              }
            }
          }
          me{
            id
          }
        }
    """

    # when
    staff_api_client.user.user_permissions.add(permission_manage_products)
    staff_api_client.post_graphql(query)
    span = get_span_by_name(get_test_spans(), "graphql_query")

    # then
    assert span.attributes["graphql.query_identifier"] == "me, products"


def test_tracing_query_identifier_with_fragment(
    staff_api_client,
    permission_manage_products,
    get_test_spans,
):
    query = """
        fragment ProductVariant on ProductVariant {
          id
        }
        query test {
          products(first:5) {
            edges{
              node{
                id
                name
                variants {
                  ...ProductVariant
                }
              }
            }
          }
        }
    """
    staff_api_client.user.user_permissions.add(permission_manage_products)

    # when
    staff_api_client.post_graphql(query)
    span = get_span_by_name(get_test_spans(), "graphql_query")

    # then
    assert span.attributes["graphql.query_identifier"] == "products"


def test_tracing_query_identifier_for_unnamed_mutation(
    staff_api_client,
    get_test_spans,
):
    # given
    query = """
        mutation{
          tokenCreate(email: "admin@example.com", password:"admin"){
            token
          }
        }
    """

    # when
    staff_api_client.post_graphql(query)
    span = get_span_by_name(get_test_spans(), "graphql_query")

    # then
    assert span.attributes["graphql.query_identifier"] == "tokenCreate"


def test_tracing_query_identifier_for_named_mutation(
    staff_api_client,
    get_test_spans,
):
    # given
    query = """
        mutation MutationName{
          tokenCreate(email: "admin@example.com", password:"admin"){
            token
          }
        }
    """

    # when
    staff_api_client.post_graphql(query)
    span = get_span_by_name(get_test_spans(), "graphql_query")

    # then
    assert span.attributes["graphql.query_identifier"] == "tokenCreate"


def test_tracing_query_identifier_for_many_mutations(
    staff_api_client,
    get_test_spans,
):
    # given
    query = """
      mutation {
        tokenCreate(email: "admin@example.com", password:"admin"){
          token
          refreshToken
          csrfToken
        }
        deleteWarehouse(id:""){
          errors{
            field
          }
        }
      }
    """

    # when
    staff_api_client.post_graphql(query)
    span = get_span_by_name(get_test_spans(), "graphql_query")

    # then
    assert span.attributes["graphql.query_identifier"] == "deleteWarehouse, tokenCreate"


def test_tracing_query_identifier_undefined(
    staff_api_client,
    permission_manage_products,
    get_test_spans,
):
    # given
    query = """
        fragment ProductVariant on ProductVariant {
          id
        }
    """
    staff_api_client.user.user_permissions.add(permission_manage_products)

    # when
    staff_api_client.post_graphql(query)
    span = get_span_by_name(get_test_spans(), "graphql_query")

    # then
    assert span.attributes["graphql.query_identifier"] == "undefined"


def test_tracing_dont_have_app_data_staff_as_requestor(
    staff_api_client,
    permission_manage_products,
    get_test_spans,
):
    # given
    query = """
        query test {
          products(first:5) {
            edges{
              node{
                id
                name
              }
            }
          }
        }
    """
    staff_api_client.user.user_permissions.add(permission_manage_products)

    # when
    staff_api_client.post_graphql(query)
    span = get_span_by_name(get_test_spans(), "graphql_query")

    # then
    assert "app.name" not in span.attributes
    assert "app.id" not in span.attributes


def test_tracing_have_app_data_app_as_requestor(
    app_api_client,
    permission_manage_products,
    get_test_spans,
):
    # given
    query = """
        query test {
          products(first:5) {
            edges{
              node{
                id
                name
              }
            }
          }
        }
    """
    app = app_api_client.app
    app.permissions.add(permission_manage_products)

    # when
    app_api_client.post_graphql(query)
    span = get_span_by_name(get_test_spans(), "graphql_query")

    # then
    assert span.attributes["app.name"] == app.name
    assert span.attributes["app.id"] == app.id


@pytest.mark.parametrize(
    ("header_source", "expected_result"),
    [
        ("saleor.dashboard", "saleor.dashboard"),
        ("saleor.dashboard.playground", "saleor.dashboard.playground"),
        ("saleor.playground", "saleor.playground"),
        ("saleor.DASHBOARD", "saleor.dashboard"),
        ("SALEOR.dashboard", "saleor.dashboard"),
        ("saleor.dashboard.Playground", "saleor.dashboard.playground"),
        ("saleor.playgrounD", "saleor.playground"),
        ("incorrect-value", "unknown_service"),
        (None, "unknown_service"),
    ],
)
def test_tracing_have_source_service_name_set(
    header_source,
    expected_result,
    app_api_client,
    permission_manage_products,
    get_test_spans,
):
    # given
    query = """
        query test {
          products(first:5) {
            edges{
              node{
                id
                name
              }
            }
          }
        }
    """
    app = app_api_client.app
    app.permissions.add(permission_manage_products)

    # when
    app_api_client.post_graphql(query, headers={"source-service-name": header_source})

    # then
    span = get_span_by_name(get_test_spans(), "graphql_query")
    assert span.attributes["source.service.name"] == expected_result


@pytest.mark.parametrize(
    ("data", "error_message"),
    [
        ("", "Must provide a query string."),
        (
            {"query": "{"},
            "Syntax Error GraphQL (1:2) Expected Name, found EOF\n\n1: {\n    ^\n",
        ),
        (
            {
                "query": "query { ... { __schema { __typename } } ... { shop { name } } }"
            },
            "Queries and introspection cannot be mixed in the same request.",
        ),
        (
            {"query": "{ products(first: 9999999999) { edges { node { id } } } }"},
            'Argument "first" has invalid value 9999999999.\nExpected type "Int", found 9999999999.',
        ),
    ],
)
@patch("saleor.core.telemetry.tracer.start_as_current_span")
def test_graphql_query_span_set_status_error_invalid_query(
    mock_start_span,
    data,
    error_message,
    rf,
):
    # given
    mock_span = MagicMock()
    mock_start_span.return_value.__enter__.return_value = mock_span

    request = rf.post(
        path="/graphql",
        data=data,
        content_type="application/json",
    )

    # when
    view = GraphQLView.as_view(backend=backend, schema=schema)
    view(request)

    # then
    mock_span.set_status.assert_called_once_with(
        status=StatusCode.ERROR, description=error_message
    )


@override_settings(GRAPHQL_QUERY_MAX_COMPLEXITY=1)
@patch("saleor.core.telemetry.tracer.start_as_current_span")
def test_graphql_query_span_set_status_error_cost_exceeded(
    mock_start_span,
    api_client,
    variant_with_many_stocks,
    channel_USD,
):
    # given
    mock_span = MagicMock()
    mock_start_span.return_value.__enter__.return_value = mock_span

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
    response = api_client.post_graphql(query, variables)

    # then
    json_response = response.json()
    query_cost = json_response["extensions"]["cost"]["requestedQueryCost"]
    expected_error_message = (
        f"The query exceeds the maximum cost of 1. Actual cost is {query_cost}"
    )
    mock_span.set_status.assert_called_once_with(
        status=StatusCode.ERROR, description=expected_error_message
    )
