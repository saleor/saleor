import logging
from unittest import mock

import graphene
import pytest
from django.test import override_settings

from saleor.demo.views import EXAMPLE_QUERY
from saleor.graphql.product.types import Product
from saleor.graphql.views import handled_errors_logger, unhandled_errors_logger

from .conftest import API_PATH
from .utils import _get_graphql_content_from_response, get_graphql_content


def test_batch_queries(category, product, api_client):
    query_product = """
        query GetProduct($id: ID!) {
            product(id: $id) {
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
            "variables": {"id": graphene.Node.to_global_id("Category", category.pk)},
        },
        {
            "query": query_product,
            "variables": {"id": graphene.Node.to_global_id("Product", product.pk)},
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


def test_invalid_request_body_non_debug(client):
    data = "invalid-data"
    response = client.post(API_PATH, data, content_type="application/json")
    assert response.status_code == 400
    content = _get_graphql_content_from_response(response)
    assert "errors" in content


@override_settings(DEBUG=True)
def test_invalid_request_body_with_debug(client):
    data = "invalid-data"
    response = client.post(API_PATH, data, content_type="application/json")
    assert response.status_code == 400
    content = _get_graphql_content_from_response(response)
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
    content = _get_graphql_content_from_response(response)
    assert "errors" in content


def test_no_query(client):
    response = client.post(API_PATH, "", content_type="application/json")
    assert response.status_code == 400
    content = _get_graphql_content_from_response(response)
    assert content["errors"][0]["message"] == "Must provide a query string."


def test_query_is_dict(client):
    data = {"query": {"type": "dict"}}
    response = client.post(API_PATH, data, content_type="application/json")
    assert response.status_code == 400
    content = _get_graphql_content_from_response(response)
    assert content["errors"][0]["message"] == "Must provide a query string."


def test_graphql_execution_exception(monkeypatch, api_client):
    def mocked_execute(*args, **kwargs):
        raise IOError("Spanish inquisition")

    monkeypatch.setattr("graphql.backend.core.execute_and_validate", mocked_execute)
    response = api_client.post_graphql("{ shop { name }}")
    assert response.status_code == 400
    content = _get_graphql_content_from_response(response)
    assert content["errors"][0]["message"] == "Spanish inquisition"


class LoggingHandler(logging.Handler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.messages = []

    def emit(self, record: logging.LogRecord):
        exc_type, exc_value, _tb = record.exc_info
        self.messages.append(
            f"{record.name}[{record.levelname.upper()}].{exc_type.__name__}"
        )


@pytest.fixture
def graphql_log_handler():
    log_handler = LoggingHandler()

    unhandled_errors_logger.addHandler(log_handler)
    handled_errors_logger.addHandler(log_handler)

    return log_handler


def test_invalid_query_graphql_errors_are_logged_in_another_logger(
    api_client, graphql_log_handler
):
    response = api_client.post_graphql("{ shop }")
    assert response.status_code == 400
    assert graphql_log_handler.messages == [
        "saleor.graphql.errors.handled[ERROR].GraphQLError"
    ]


def test_invalid_syntax_graphql_errors_are_logged_in_another_logger(
    api_client, graphql_log_handler
):
    response = api_client.post_graphql("{ }")
    assert response.status_code == 400
    assert graphql_log_handler.messages == [
        "saleor.graphql.errors.handled[ERROR].GraphQLSyntaxError"
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
        "saleor.graphql.errors.handled[ERROR].PermissionDenied"
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


@mock.patch.object(Product, "get_node")
def test_unexpected_exceptions_are_logged_in_their_own_logger(
    mocked_get_node, staff_api_client, graphql_log_handler, permission_manage_products
):
    def bad_get_node(info, pk):
        raise NotImplementedError(info, pk)

    mocked_get_node.side_effect = bad_get_node

    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(
        '{ product(id: "UHJvZHVjdDoxMg==") { name } }'
    )

    assert response.status_code == 200
    assert graphql_log_handler.messages == [
        "saleor.graphql.errors.unhandled[ERROR].NotImplementedError"
    ]


def test_example_query(api_client, product):
    response = api_client.post_graphql(EXAMPLE_QUERY)
    content = get_graphql_content(response)
    assert content["data"]["products"]["edges"][0]["node"]["name"] == product.name
