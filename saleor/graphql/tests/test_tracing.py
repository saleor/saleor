import hashlib

import graphene
import pytest
from opentelemetry import trace as trace_api
from opentelemetry.sdk.trace import TracerProvider, export
from opentelemetry.sdk.trace.export.in_memory_span_exporter import (
    InMemorySpanExporter,
)

from ...core.telemetry import initialize_telemetry


@pytest.fixture(scope="session", autouse=True)
def in_memory_span_exporter():
    span_exporter = InMemorySpanExporter()
    exporter_processor = export.SimpleSpanProcessor(span_exporter)
    provider = TracerProvider()
    provider.add_span_processor(exporter_processor)
    trace_api.set_tracer_provider(provider)
    initialize_telemetry()
    return span_exporter


@pytest.fixture
def get_test_spans(in_memory_span_exporter):
    in_memory_span_exporter.clear()

    def get_and_clear_spans():
        spans = in_memory_span_exporter.get_finished_spans()
        in_memory_span_exporter.clear()
        return spans

    return get_and_clear_spans


def _get_graphql_span(spans):
    return next(_get_graphql_spans(spans))


def _get_graphql_spans(spans):
    return filter(lambda item: item.attributes.get("graphql.query_fingerprint"), spans)


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
    span = _get_graphql_span(get_test_spans())

    # then
    assert span
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
    span = _get_graphql_span(get_test_spans())

    # then
    assert span
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
        for span in _get_graphql_spans(get_test_spans())
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
    span = _get_graphql_span(get_test_spans())

    # then
    assert span
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
    span = _get_graphql_span(get_test_spans())

    # then
    assert span
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
        mutation, variables, permissions=[permission_manage_orders]
    )
    span = _get_graphql_span(get_test_spans())

    # then
    assert span
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
    span = _get_graphql_span(get_test_spans())

    # then
    assert span
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
    span = _get_graphql_span(get_test_spans())

    # then
    assert span
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
    span = _get_graphql_span(get_test_spans())

    # then
    assert span
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
    span = _get_graphql_span(get_test_spans())

    # then
    assert span
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
    span = _get_graphql_span(get_test_spans())

    # then
    assert span
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
    span = _get_graphql_span(get_test_spans())

    # then
    assert span
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
    span = _get_graphql_span(get_test_spans())

    # then
    assert span
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
    span = _get_graphql_span(get_test_spans())

    # then
    assert span
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
    spans = list(
        filter(lambda s: s.attributes.get("source.service.name"), get_test_spans())
    )
    assert len(spans) == 1
    span = spans[0]
    assert span.attributes["source.service.name"] == expected_result
