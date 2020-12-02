from unittest import mock

import graphene
import pytest
from django.test import override_settings

from ....demo.views import EXAMPLE_QUERY
from ...tests.fixtures import (
    ACCESS_CONTROL_ALLOW_CREDENTIALS,
    ACCESS_CONTROL_ALLOW_HEADERS,
    ACCESS_CONTROL_ALLOW_METHODS,
    ACCESS_CONTROL_ALLOW_ORIGIN,
    API_PATH,
)
from ...tests.utils import get_graphql_content, get_graphql_content_from_response


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


@pytest.mark.parametrize("playground_on, status", [(True, 200), (False, 405)])
def test_graphql_view_get_enabled_or_disabled(client, settings, playground_on, status):
    settings.PLAYGROUND_ENABLED = playground_on
    response = client.get(API_PATH)
    assert response.status_code == status


def test_graphql_view_options(client):
    response = client.options(API_PATH)
    assert response.status_code == 200


@pytest.mark.parametrize("method", ("put", "patch", "delete"))
def test_graphql_view_not_allowed(method, client):
    func = getattr(client, method)
    response = func(API_PATH)
    assert response.status_code == 405


def test_graphql_view_access_control_header(client, settings):
    settings.ALLOWED_GRAPHQL_ORIGINS = ["*"]
    origin = "http://localhost:3000"
    response = client.options(API_PATH, HTTP_ORIGIN=origin)
    assert response[ACCESS_CONTROL_ALLOW_ORIGIN] == origin
    assert response[ACCESS_CONTROL_ALLOW_CREDENTIALS] == "true"
    assert response[ACCESS_CONTROL_ALLOW_METHODS] == "POST, OPTIONS"
    assert (
        response[ACCESS_CONTROL_ALLOW_HEADERS]
        == "Origin, Content-Type, Accept, Authorization"
    )

    response = client.options(API_PATH)
    assert all(
        [
            field not in response
            for field in (
                ACCESS_CONTROL_ALLOW_ORIGIN,
                ACCESS_CONTROL_ALLOW_CREDENTIALS,
                ACCESS_CONTROL_ALLOW_HEADERS,
                ACCESS_CONTROL_ALLOW_METHODS,
            )
        ]
    )


@pytest.mark.parametrize(
    "allowed_origins,allowed,not_allowed",
    [
        (
            ["*"],
            [
                "http://example.org",
                "https://example.org",
                "http://localhost:3000",
                "http://localhost:9000",
                "file://",
            ],
            [],
        ),
        (
            ["http://example.org"],
            ["http://example.org"],
            [
                "https://example.org",
                "http://localhost:3000",
                "http://localhost:9000",
                "file://",
            ],
        ),
        (
            ["http://example.org", "https://example.org"],
            ["http://example.org", "https://example.org"],
            ["http://localhost:3000", "http://localhost:9000", "file://"],
        ),
        (
            ["http://localhost:3000", "http://localhost:9000"],
            ["http://localhost:3000", "http://localhost:9000"],
            ["http://example.org", "https://example.org", "file://"],
        ),
    ],
)
def test_graphql_view_access_control_allowed_origins(
    client, settings, allowed_origins, allowed, not_allowed
):
    settings.ALLOWED_GRAPHQL_ORIGINS = allowed_origins
    for origin in allowed:
        response = client.options(API_PATH, HTTP_ORIGIN=origin)
        assert response[ACCESS_CONTROL_ALLOW_ORIGIN] == origin
    for origin in not_allowed:
        response = client.options(API_PATH, HTTP_ORIGIN=origin)
        assert ACCESS_CONTROL_ALLOW_ORIGIN not in response


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
    assert content["errors"][0]["message"] == "Spanish inquisition"


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
          productImageDelete(id: "aa") {
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
          productImageDelete(id: "aa") {
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
