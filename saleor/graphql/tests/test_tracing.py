import datetime
import hashlib
import json
from unittest.mock import MagicMock, patch

import graphene
import pytest
from django.test import override_settings
from opentelemetry.semconv._incubating.attributes import graphql_attributes
from opentelemetry.trace import StatusCode
from requests_hardened import HTTPSession

from ...core.telemetry import saleor_attributes
from ...graphql.api import backend, schema
from ...tests.utils import filter_spans_by_name, get_span_by_name
from ..views import GraphQLView


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
    span = get_span_by_name(get_test_spans(), query)

    # then
    hash = hashlib.md5(
        span.attributes[graphql_attributes.GRAPHQL_DOCUMENT].encode("utf-8")
    ).hexdigest()
    assert (
        span.attributes[saleor_attributes.GRAPHQL_DOCUMENT_FINGERPRINT]
        == f"query:test:{hash}"
    )


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
    span = get_span_by_name(get_test_spans(), query)

    # then
    hash = hashlib.md5(
        span.attributes[graphql_attributes.GRAPHQL_DOCUMENT].encode("utf-8")
    ).hexdigest()
    assert (
        span.attributes[saleor_attributes.GRAPHQL_DOCUMENT_FINGERPRINT]
        == f"query:test:{hash}"
    )


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
        span.attributes[saleor_attributes.GRAPHQL_DOCUMENT_FINGERPRINT]
        for span in filter_spans_by_name(get_test_spans(), query)
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
    span = get_span_by_name(get_test_spans(), query)

    # then
    hash = hashlib.md5(
        span.attributes[graphql_attributes.GRAPHQL_DOCUMENT].encode("utf-8")
    ).hexdigest()
    assert (
        span.attributes[saleor_attributes.GRAPHQL_DOCUMENT_FINGERPRINT]
        == f"query:{hash}"
    )


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
    span = get_span_by_name(get_test_spans(), query)

    # then
    hash = hashlib.md5(
        span.attributes[graphql_attributes.GRAPHQL_DOCUMENT].encode("utf-8")
    ).hexdigest()
    assert (
        span.attributes[saleor_attributes.GRAPHQL_DOCUMENT_FINGERPRINT]
        == f"query:{hash}"
    )


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
    span = get_span_by_name(get_test_spans(), mutation)

    # then
    hash = hashlib.md5(
        span.attributes[graphql_attributes.GRAPHQL_DOCUMENT].encode("utf-8")
    ).hexdigest()
    assert (
        span.attributes[saleor_attributes.GRAPHQL_DOCUMENT_FINGERPRINT]
        == f"mutation:cancelOrder:{hash}"
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
    span = get_span_by_name(get_test_spans(), query)

    # then
    assert (
        span.attributes[saleor_attributes.GRAPHQL_OPERATION_IDENTIFIER]
        == "me, products"
    )


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
    span = get_span_by_name(get_test_spans(), query)

    # then
    assert span.attributes[saleor_attributes.GRAPHQL_OPERATION_IDENTIFIER] == "products"


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
    span = get_span_by_name(get_test_spans(), query)

    # then
    assert (
        span.attributes[saleor_attributes.GRAPHQL_OPERATION_IDENTIFIER] == "tokenCreate"
    )


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
    span = get_span_by_name(get_test_spans(), query)

    # then
    assert (
        span.attributes[saleor_attributes.GRAPHQL_OPERATION_IDENTIFIER] == "tokenCreate"
    )


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
    span = get_span_by_name(get_test_spans(), query)

    # then
    assert (
        span.attributes[saleor_attributes.GRAPHQL_OPERATION_IDENTIFIER]
        == "deleteWarehouse, tokenCreate"
    )


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
    span = get_span_by_name(get_test_spans(), query)

    # then
    assert (
        span.attributes[saleor_attributes.GRAPHQL_OPERATION_IDENTIFIER] == "undefined"
    )


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
    span = get_span_by_name(get_test_spans(), query)

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
    span = get_span_by_name(get_test_spans(), query)

    # then
    assert span.attributes[saleor_attributes.SALEOR_APP_NAME] == app.name
    assert span.attributes[saleor_attributes.SALEOR_APP_ID] == app.id


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
    span = get_span_by_name(get_test_spans(), query)
    assert (
        span.attributes[saleor_attributes.SALEOR_SOURCE_SERVICE_NAME] == expected_result
    )


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


def test_trace_context_propagation(
    trace_context_propagation, user_api_client, get_test_spans
):
    # given
    formatted_trace_id = "d30f57682d56377acf27bbef17042d9a"
    formatted_parent_span_id = "b63e859130b3cabf"
    trace_state = "rojo=00f067aa0ba902b7"
    query = """
        {
          shop {
            name
          }
        }
    """

    # when
    response = user_api_client.post_graphql(
        query,
        headers={
            "traceparent": f"00-{formatted_trace_id}-{formatted_parent_span_id}-01",
            "tracestate": trace_state,
        },
    )

    # then
    span = get_span_by_name(get_test_spans(), "/graphql/")
    assert format(span.context.trace_id, "032x") == formatted_trace_id
    assert format(span.parent.span_id, "016x") == formatted_parent_span_id
    assert "traceparent" in response.headers
    assert "tracestate" in response.headers
    assert (
        response.headers["traceparent"]
        == f"00-{formatted_trace_id}-{format(span.context.span_id, '016x')}-01"
    )
    assert response.headers["tracestate"] == trace_state


@patch.object(HTTPSession, "request")
@override_settings(
    PLUGINS=["saleor.plugins.webhook.plugin.WebhookPlugin"],
    CHECKOUT_PRICES_TTL=datetime.timedelta(0),
)
def test_trace_context_propagation_in_sync_webhook(
    mock_request,
    trace_context_propagation,
    user_api_client,
    get_test_spans,
    tax_app,
    checkout_with_item,
):
    # given
    tax_app_response = {
        "shipping_tax_rate": "10.00",
        "shipping_price_gross_amount": "110.00",
        "shipping_price_net_amount": "100.00",
        "lines": [
            {
                "tax_rate": "20.00",
                "total_gross_amount": "120.00",
                "total_net_amount": "100.00",
            },
        ],
    }
    mock_request.return_value = MagicMock(
        text=json.dumps(tax_app_response),
        headers={"response": "header"},
        elapsed=datetime.timedelta(seconds=1),
        status_code=200,
        ok=True,
    )

    formatted_trace_id = "d30f57682d56377acf27bbef17042d9a"
    formatted_parent_span_id = "b63e859130b3cabf"
    trace_state = "rojo=00f067aa0ba902b7"

    query = """
        query checkout($id: ID!) {
          checkout(id: $id) {
            id
            totalPrice {
              gross {
                currency
                amount
              }
            }
          }
        }
    """

    # when
    user_api_client.post_graphql(
        query,
        variables={"id": graphene.Node.to_global_id("Checkout", checkout_with_item.pk)},
        headers={
            "traceparent": f"00-{formatted_trace_id}-{formatted_parent_span_id}-01",
            "tracestate": trace_state,
        },
    )

    # then
    call_headers = mock_request.call_args[1]["headers"]
    span = get_span_by_name(get_test_spans(), "webhooks.checkout_calculate_taxes")
    assert format(span.context.trace_id, "032x") == formatted_trace_id
    assert "traceparent" in call_headers
    assert "tracestate" in call_headers
    assert (
        call_headers["traceparent"]
        == f"00-{formatted_trace_id}-{format(span.context.span_id, '016x')}-01"
    )
    assert call_headers["tracestate"] == trace_state
