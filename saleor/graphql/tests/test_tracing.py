import hashlib
from unittest.mock import MagicMock, patch

import graphene
import pytest


class MockTracer(MagicMock):
    # TODO: This is added only to make the linters work. It should be removed
    # after tests are reworked.
    pass


def _get_graphql_span(spans):
    return next(_get_graphql_spans(spans))


def _get_graphql_spans(spans):
    return filter(lambda item: item.tags.get("graphql.query_fingerprint"), spans)


@pytest.mark.skip(reason="Adjust tracing tests when to use OpenTelemetry")
@patch("saleor.graphql.views.opentracing.global_tracer")
def test_tracing_query_hashing(
    tracing_mock,
    staff_api_client,
    permission_manage_products,
):
    # given
    tracer = MockTracer()
    tracing_mock.return_value = tracer
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
    span = _get_graphql_span(tracer.finished_spans())

    # then
    hash = hashlib.md5(span.tags["graphql.query"].encode("utf-8")).hexdigest()
    assert span.tags["graphql.query_fingerprint"] == f"query:test:{hash}"


@pytest.mark.skip(reason="Adjust tracing tests when to use OpenTelemetry")
@patch("saleor.graphql.views.opentracing.global_tracer")
def test_tracing_query_hashing_with_fragment(
    tracing_mock,
    staff_api_client,
    permission_manage_products,
):
    # given
    tracer = MockTracer()
    tracing_mock.return_value = tracer
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
    span = _get_graphql_span(tracer.finished_spans())

    # then
    hash = hashlib.md5(span.tags["graphql.query"].encode("utf-8")).hexdigest()
    assert span.tags["graphql.query_fingerprint"] == f"query:test:{hash}"


@pytest.mark.skip(reason="Adjust tracing tests when to use OpenTelemetry")
@patch("saleor.graphql.views.opentracing.global_tracer")
def test_tracing_query_hashing_different_vars_same_checksum(
    tracing_mock,
    staff_api_client,
    permission_manage_products,
):
    # given
    tracer = MockTracer()
    tracing_mock.return_value = tracer
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
        span.tags["graphql.query_fingerprint"]
        for span in _get_graphql_spans(tracer.finished_spans())
    ]
    assert len(fingerprints) == QUERIES
    assert len(set(fingerprints)) == 1


@pytest.mark.skip(reason="Adjust tracing tests when to use OpenTelemetry")
@patch("saleor.graphql.views.opentracing.global_tracer")
def test_tracing_query_hashing_unnamed_query(
    tracing_mock,
    staff_api_client,
    permission_manage_products,
):
    # given
    tracer = MockTracer()
    tracing_mock.return_value = tracer
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
    span = _get_graphql_span(tracer.finished_spans())

    # then
    hash = hashlib.md5(span.tags["graphql.query"].encode("utf-8")).hexdigest()
    assert span.tags["graphql.query_fingerprint"] == f"query:{hash}"


@pytest.mark.skip(reason="Adjust tracing tests when to use OpenTelemetry")
@patch("saleor.graphql.views.opentracing.global_tracer")
def test_tracing_query_hashing_unnamed_query_no_query_spec(
    tracing_mock,
    staff_api_client,
    permission_manage_products,
):
    # given
    tracer = MockTracer()
    tracing_mock.return_value = tracer
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
    span = _get_graphql_span(tracer.finished_spans())

    # then
    hash = hashlib.md5(span.tags["graphql.query"].encode("utf-8")).hexdigest()
    assert span.tags["graphql.query_fingerprint"] == f"query:{hash}"


@pytest.mark.skip(reason="Adjust tracing tests when to use OpenTelemetry")
@patch("saleor.graphql.views.opentracing.global_tracer")
def test_tracing_mutation_hashing(
    tracing_mock,
    staff_api_client,
    permission_manage_orders,
    order_with_lines,
):
    # given
    tracer = MockTracer()
    tracing_mock.return_value = tracer
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
    span = _get_graphql_span(tracer.finished_spans())

    # then
    hash = hashlib.md5(span.tags["graphql.query"].encode("utf-8")).hexdigest()
    assert span.tags["graphql.query_fingerprint"] == f"mutation:cancelOrder:{hash}"


@pytest.mark.skip(reason="Adjust tracing tests when to use OpenTelemetry")
@patch("saleor.graphql.views.opentracing.global_tracer")
def test_tracing_query_identifier_for_query(
    tracing_mock,
    staff_api_client,
    permission_manage_products,
):
    # given
    tracer = MockTracer()
    tracing_mock.return_value = tracer
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
    staff_api_client.user.user_permissions.add(permission_manage_products)
    staff_api_client.post_graphql(query)
    span = _get_graphql_span(tracer.finished_spans())
    assert span.tags["graphql.query_identifier"] == "me, products"


@pytest.mark.skip(reason="Adjust tracing tests when to use OpenTelemetry")
@patch("saleor.graphql.views.opentracing.global_tracer")
def test_tracing_query_identifier_with_fragment(
    tracing_mock,
    staff_api_client,
    permission_manage_products,
):
    tracer = MockTracer()
    tracing_mock.return_value = tracer
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
    span = _get_graphql_span(tracer.finished_spans())

    # then
    assert span.tags["graphql.query_identifier"] == "products"


@pytest.mark.skip(reason="Adjust tracing tests when to use OpenTelemetry")
@patch("saleor.graphql.views.opentracing.global_tracer")
def test_tracing_query_identifier_for_unnamed_mutation(
    tracing_mock,
    staff_api_client,
):
    # given
    tracer = MockTracer()
    tracing_mock.return_value = tracer
    query = """
        mutation{
          tokenCreate(email: "admin@example.com", password:"admin"){
            token
          }
        }
    """

    # when
    staff_api_client.post_graphql(query)
    span = _get_graphql_span(tracer.finished_spans())

    # then
    assert span.tags["graphql.query_identifier"] == "tokenCreate"


@pytest.mark.skip(reason="Adjust tracing tests when to use OpenTelemetry")
@patch("saleor.graphql.views.opentracing.global_tracer")
def test_tracing_query_identifier_for_named_mutation(
    tracing_mock,
    staff_api_client,
):
    # given
    tracer = MockTracer()
    tracing_mock.return_value = tracer
    query = """
        mutation MutationName{
          tokenCreate(email: "admin@example.com", password:"admin"){
            token
          }
        }
    """

    # when
    staff_api_client.post_graphql(query)
    span = _get_graphql_span(tracer.finished_spans())

    # then
    assert span.tags["graphql.query_identifier"] == "tokenCreate"


@pytest.mark.skip(reason="Adjust tracing tests when to use OpenTelemetry")
@patch("saleor.graphql.views.opentracing.global_tracer")
def test_tracing_query_identifier_for_many_mutations(
    tracing_mock,
    staff_api_client,
):
    # given
    tracer = MockTracer()
    tracing_mock.return_value = tracer
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
    span = _get_graphql_span(tracer.finished_spans())

    # then
    assert span.tags["graphql.query_identifier"] == "deleteWarehouse, tokenCreate"


@pytest.mark.skip(reason="Adjust tracing tests when to use OpenTelemetry")
@patch("saleor.graphql.views.opentracing.global_tracer")
def test_tracing_query_identifier_undefined(
    tracing_mock,
    staff_api_client,
    permission_manage_products,
):
    # given
    tracer = MockTracer()
    tracing_mock.return_value = tracer
    query = """
        fragment ProductVariant on ProductVariant {
          id
        }
    """
    staff_api_client.user.user_permissions.add(permission_manage_products)

    # when
    staff_api_client.post_graphql(query)
    span = _get_graphql_span(tracer.finished_spans())

    # then
    assert span.tags["graphql.query_identifier"] == "undefined"


@pytest.mark.skip(reason="Adjust tracing tests when to use OpenTelemetry")
@patch("saleor.graphql.views.opentracing.global_tracer")
def test_tracing_dont_have_app_data_staff_as_requestor(
    tracing_mock,
    staff_api_client,
    permission_manage_products,
):
    # given
    tracer = MockTracer()
    tracing_mock.return_value = tracer
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
    span = _get_graphql_span(tracer.finished_spans())

    # then
    assert "app.name" not in span.tags
    assert "app.id" not in span.tags


@pytest.mark.skip(reason="Adjust tracing tests when to use OpenTelemetry")
@patch("saleor.graphql.views.opentracing.global_tracer")
def test_tracing_have_app_data_app_as_requestor(
    tracing_mock,
    app_api_client,
    permission_manage_products,
):
    # given
    tracer = MockTracer()
    tracing_mock.return_value = tracer
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
    span = _get_graphql_span(tracer.finished_spans())

    # then
    assert span.tags["app.name"] == app.name
    assert span.tags["app.id"] == app.id
