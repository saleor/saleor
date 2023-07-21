from unittest import mock

import graphene
import pytest
from django.test import override_settings
from graphql.execution.base import ExecutionResult

from .... import __version__ as saleor_version
from ....demo.views import EXAMPLE_QUERY
from ....graphql.utils import INTERNAL_ERROR_MESSAGE
from ...tests.fixtures import API_PATH
from ...tests.utils import get_graphql_content, get_graphql_content_from_response
from ...views import generate_cache_key


def test_batch_queries(category, product, api_client, channel_USD):
    query_product = """
        query GetProduct($id: ID!, $channel: String) {
            product(id: $id, channel: $channel) {
                name
            }
        }
    """
    query_category = """
        query GetCategory($id: ID!) {
            category(id: $id) {
                name
            }
        }
    """
    data = [
        {
            "query": query_category,
            "variables": {
                "id": graphene.Node.to_global_id("Category", category.pk),
                "channel": channel_USD.slug,
            },
        },
        {
            "query": query_product,
            "variables": {
                "id": graphene.Node.to_global_id("Product", product.pk),
                "channel": channel_USD.slug,
            },
        },
    ]
    response = api_client.post(data)
    batch_content = get_graphql_content(response)
    assert "errors" not in batch_content
    assert isinstance(batch_content, list)
    assert len(batch_content) == 2

    data = {
        field: value
        for content in batch_content
        for field, value in content["data"].items()
    }
    assert data["product"]["name"] == product.name
    assert data["category"]["name"] == category.name


def test_graphql_view_query_with_invalid_object_type(
    staff_api_client, product, permission_manage_orders, graphql_log_handler
):
    query = """
    query($id: ID!) {
        order(id: $id){
            token
        }
    }
    """
    variables = {
        "id": graphene.Node.to_global_id("Product", product.pk),
    }
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(query, variables=variables)
    content = get_graphql_content(response)
    assert content["data"]["order"] is None


@pytest.mark.parametrize("playground_on, status", [(True, 200), (False, 405)])
def test_graphql_view_get_enabled_or_disabled(client, settings, playground_on, status):
    settings.PLAYGROUND_ENABLED = playground_on
    response = client.get(API_PATH)
    assert response.status_code == status


@pytest.mark.parametrize("method", ("put", "patch", "delete"))
def test_graphql_view_not_allowed(method, client):
    func = getattr(client, method)
    response = func(API_PATH)
    assert response.status_code == 405


def test_invalid_request_body_non_debug(client):
    data = "invalid-data"
    response = client.post(API_PATH, data, content_type="application/json")
    assert response.status_code == 400
    content = get_graphql_content_from_response(response)
    assert "errors" in content


@override_settings(DEBUG=True)
def test_invalid_request_body_with_debug(client):
    data = "invalid-data"
    response = client.post(API_PATH, data, content_type="application/json")
    assert response.status_code == 400
    content = get_graphql_content_from_response(response)
    errors = content.get("errors")
    assert errors == [
        {
            "extensions": {"exception": {"code": "str", "stacktrace": []}},
            "message": "Unable to parse query.",
        }
    ]


def test_invalid_query(api_client):
    query = "query { invalid }"
    response = api_client.post_graphql(query, check_no_permissions=False)
    assert response.status_code == 400
    content = get_graphql_content_from_response(response)
    assert "errors" in content


def test_no_query(client):
    response = client.post(API_PATH, "", content_type="application/json")
    assert response.status_code == 400
    content = get_graphql_content_from_response(response)
    assert content["errors"][0]["message"] == "Must provide a query string."


def test_query_is_dict(client):
    data = {"query": {"type": "dict"}}
    response = client.post(API_PATH, data, content_type="application/json")
    assert response.status_code == 400
    content = get_graphql_content_from_response(response)
    assert content["errors"][0]["message"] == "Must provide a query string."


def test_graphql_execution_exception(monkeypatch, api_client):
    def mocked_execute(*args, **kwargs):
        raise IOError("Spanish inquisition")

    monkeypatch.setattr("graphql.backend.core.execute_and_validate", mocked_execute)
    response = api_client.post_graphql("{ shop { name }}")
    assert response.status_code == 400
    content = get_graphql_content_from_response(response)
    assert content["errors"][0]["message"] == INTERNAL_ERROR_MESSAGE


def test_invalid_query_graphql_errors_are_logged_in_another_logger(
    api_client, graphql_log_handler
):
    response = api_client.post_graphql("{ shop }")
    assert response.status_code == 400
    assert graphql_log_handler.messages == [
        "saleor.graphql.errors.handled[INFO].GraphQLError"
    ]


def test_invalid_syntax_graphql_errors_are_logged_in_another_logger(
    api_client, graphql_log_handler
):
    response = api_client.post_graphql("{ }")
    assert response.status_code == 400
    assert graphql_log_handler.messages == [
        "saleor.graphql.errors.handled[INFO].GraphQLSyntaxError"
    ]


def test_permission_denied_query_graphql_errors_are_logged_in_another_logger(
    api_client, graphql_log_handler
):
    response = api_client.post_graphql(
        """
        mutation {
          productMediaDelete(id: "aa") {
            errors {
              message
            }
          }
        }
        """
    )
    assert response.status_code == 200
    assert graphql_log_handler.messages == [
        "saleor.graphql.errors.handled[INFO].PermissionDenied"
    ]


def test_validation_errors_query_do_not_get_logged(
    staff_api_client, graphql_log_handler, permission_manage_products
):
    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(
        """
        mutation {
          productMediaDelete(id: "aa") {
            errors {
              message
            }
          }
        }
        """
    )
    assert response.status_code == 200
    assert graphql_log_handler.messages == []


@mock.patch("saleor.graphql.product.schema.resolve_collection_by_id")
def test_unexpected_exceptions_are_logged_in_their_own_logger(
    mocked_resolve_collection_by_id,
    staff_api_client,
    graphql_log_handler,
    permission_manage_products,
    published_collection,
    channel_USD,
):
    def bad_mocked_resolve_collection_by_id(info, id, channel, requestor):
        raise NotImplementedError(info, id, channel, requestor)

    mocked_resolve_collection_by_id.side_effect = bad_mocked_resolve_collection_by_id

    staff_api_client.user.user_permissions.add(permission_manage_products)
    variables = {
        "id": graphene.Node.to_global_id("Collection", published_collection.pk),
        "channel": channel_USD.slug,
    }
    response = staff_api_client.post_graphql(
        """
        query($id: ID!,$channel:String) {
            collection(id: $id,channel:$channel) {
                name
            }
        }""",
        variables=variables,
    )

    assert response.status_code == 200
    assert graphql_log_handler.messages == [
        "saleor.graphql.errors.unhandled[ERROR].NotImplementedError"
    ]


def test_example_query(api_client, product):
    response = api_client.post_graphql(EXAMPLE_QUERY)
    content = get_graphql_content(response)
    assert content["data"]["products"]["edges"][0]["node"]["name"] == product.name


@pytest.mark.parametrize(
    "other_query",
    ["me{email}", 'products(first:5,channel:"channel"){edges{node{name}}}'],
)
def test_query_contains_not_only_schema_raise_error(
    other_query, api_client, graphql_log_handler
):
    query = """
        query IntrospectionQuery {
            %(other_query)s
            __schema {
                queryType {
                    name
                }
            }
        }
        """
    response = api_client.post_graphql(query % {"other_query": other_query})
    assert response.status_code == 400
    assert graphql_log_handler.messages == [
        "saleor.graphql.errors.handled[INFO].GraphQLError"
    ]


INTROSPECTION_QUERY = """
query IntrospectionQuery {
    __schema {
        queryType {
            name
        }
    }
}
"""

INTROSPECTION_RESULT = {"__schema": {"queryType": {"name": "Query"}}}


@mock.patch("saleor.graphql.views.cache.set")
@mock.patch("saleor.graphql.views.cache.get")
@override_settings(DEBUG=False, OBSERVABILITY_REPORT_ALL_API_CALLS=False)
def test_introspection_query_is_cached(cache_get_mock, cache_set_mock, api_client):
    cache_get_mock.return_value = None
    cache_key = generate_cache_key(INTROSPECTION_QUERY)
    response = api_client.post_graphql(INTROSPECTION_QUERY)
    content = get_graphql_content(response)
    assert content["data"] == INTROSPECTION_RESULT
    cache_get_mock.assert_called_once_with(cache_key)
    cache_set_mock.assert_called_once_with(
        cache_key, ExecutionResult(data=INTROSPECTION_RESULT)
    )


@mock.patch("saleor.graphql.views.cache.set")
@mock.patch("saleor.graphql.views.cache.get")
@override_settings(DEBUG=False, OBSERVABILITY_REPORT_ALL_API_CALLS=False)
def test_introspection_query_is_cached_only_once(
    cache_get_mock, cache_set_mock, api_client
):
    cache_get_mock.return_value = ExecutionResult(data=INTROSPECTION_RESULT)
    cache_key = generate_cache_key(INTROSPECTION_QUERY)
    response = api_client.post_graphql(INTROSPECTION_QUERY)
    content = get_graphql_content(response)
    assert content["data"] == INTROSPECTION_RESULT
    cache_get_mock.assert_called_once_with(cache_key)
    cache_set_mock.assert_not_called()


@mock.patch("saleor.graphql.views.cache.set")
@mock.patch("saleor.graphql.views.cache.get")
@override_settings(DEBUG=True, OBSERVABILITY_REPORT_ALL_API_CALLS=False)
def test_introspection_query_is_not_cached_in_debug_mode(
    cache_get_mock, cache_set_mock, api_client
):
    response = api_client.post_graphql(INTROSPECTION_QUERY)
    content = get_graphql_content(response)
    assert content["data"] == INTROSPECTION_RESULT
    cache_get_mock.assert_not_called()
    cache_set_mock.assert_not_called()


def test_generate_cache_key_use_saleor_version():
    cache_key = generate_cache_key(INTROSPECTION_QUERY)
    assert saleor_version in cache_key
