from functools import partial
from unittest import mock
from unittest.mock import Mock

import graphene
import pytest
from django.urls import reverse
from graphql.error import GraphQLError
from graphql_relay import to_global_id

from ....order import models as order_models
from ...core.utils import from_global_id_or_error
from ...order.types import Order
from ...product.types import Product
from ...tests.utils import get_graphql_content
from ...utils import get_nodes


def test_middleware_dont_generate_sql_requests(client, settings, assert_num_queries):
    """Test that a GET request results in no database queries."""

    # Enables the Graphql playground
    settings.DEBUG = True

    with assert_num_queries(0):
        response = client.get(reverse("api"))
        assert response.status_code == 200


def test_jwt_middleware(client, admin_user):
    # We should't base on `wsgi_request` attribute to check if user is authenticated.
    # Saleor is ASGI app, also request could be changed after response is returned.
    user_details_query = """
        {
          me {
            email
          }
        }
    """

    create_token_query = """
        mutation {
          tokenCreate(email: "admin@example.com", password: "password") {
            token
          }
        }
    """

    api_url = reverse("api")
    api_client_post = partial(client.post, api_url, content_type="application/json")

    # test setting AnonymousUser on unauthorized request to API
    response = api_client_post(data={"query": user_details_query})
    repl_data = response.json()
    assert response.status_code == 200
    assert repl_data["data"]["me"] is None

    # test creating a token for admin user
    response = api_client_post(data={"query": create_token_query})
    repl_data = response.json()
    assert response.status_code == 200
    token = repl_data["data"]["tokenCreate"]["token"]
    assert token is not None

    # test request with proper JWT token authorizes the request to API
    response = api_client_post(
        data={"query": user_details_query}, HTTP_AUTHORIZATION=f"JWT {token}"
    )
    repl_data = response.json()
    assert response.status_code == 200
    assert "errors" not in repl_data
    assert repl_data["data"]["me"] == {"email": admin_user.email}


def test_real_query(user_api_client, product, channel_USD):
    product_attr = product.product_type.product_attributes.first()
    category = product.category
    attr_value = product_attr.values.first()
    query = """
    query Root($categoryId: ID!, $sortBy: ProductOrder, $first: Int,
            $attributesFilter: [AttributeInput!], $channel: String) {

        category(id: $categoryId) {
            ...CategoryPageFragmentQuery
            __typename
        }
        products(first: $first, sortBy: $sortBy, filter: {categories: [$categoryId],
            attributes: $attributesFilter}, channel: $channel) {

            ...ProductListFragmentQuery
            __typename
        }
        attributes(first: 20, filter: {inCategory: $categoryId}, channel: $channel) {
            edges {
                node {
                    ...ProductFiltersFragmentQuery
                    __typename
                }
            }
        }
    }

    fragment CategoryPageFragmentQuery on Category {
        id
        name
        ancestors(first: 20) {
            edges {
                node {
                    name
                    id
                    __typename
                }
            }
        }
        children(first: 20) {
            edges {
                node {
                    name
                    id
                    slug
                    __typename
                }
            }
        }
        __typename
    }

    fragment ProductListFragmentQuery on ProductCountableConnection {
        edges {
            node {
                ...ProductFragmentQuery
                __typename
            }
            __typename
        }
        pageInfo {
            hasNextPage
            __typename
        }
        __typename
    }

    fragment ProductFragmentQuery on Product {
        id
        isAvailable
        name
        pricing {
            ...ProductPriceFragmentQuery
            __typename
        }
        thumbnailUrl1x: thumbnail(size: 255){
            url
        }
        thumbnailUrl2x:     thumbnail(size: 510){
            url
        }
        __typename
    }

    fragment ProductPriceFragmentQuery on ProductPricingInfo {
        discount {
            gross {
                amount
                currency
                __typename
            }
            __typename
        }
        priceRange {
            stop {
                gross {
                    amount
                    currency
                    __typename
                }
                currency
                __typename
            }
            start {
                gross {
                    amount
                    currency
                    __typename
                }
                currency
                __typename
            }
            __typename
        }
        __typename
    }

    fragment ProductFiltersFragmentQuery on Attribute {
        id
        name
        slug
        choices(first: 10) {
            edges {
                node {
                    id
                    name
                    slug
                    __typename
                }
            }
        }
        __typename
    }
    """
    variables = {
        "categoryId": graphene.Node.to_global_id("Category", category.id),
        "sortBy": {"field": "NAME", "direction": "ASC"},
        "first": 1,
        "attributesFilter": [
            {"slug": f"{product_attr.slug}", "values": [f"{attr_value.slug}"]}
        ],
        "channel": channel_USD.slug,
    }
    response = user_api_client.post_graphql(query, variables)
    get_graphql_content(response)


def test_get_nodes(product_list):
    global_ids = [to_global_id("Product", product.pk) for product in product_list]
    # Make sure function works even if duplicated ids are provided
    global_ids.append(to_global_id("Product", product_list[0].pk))
    # Return products corresponding to global ids
    products = get_nodes(global_ids, Product)
    assert products == product_list

    # Raise an error if requested id has no related database object
    nonexistent_item = Mock(type="Product", pk=-1)
    nonexistent_item_global_id = to_global_id(
        nonexistent_item.type, nonexistent_item.pk
    )
    global_ids.append(nonexistent_item_global_id)
    msg = (
        f"There is no node of type {nonexistent_item.type} with "
        f"pk {nonexistent_item.pk}"
    )
    with pytest.raises(AssertionError) as exc:
        get_nodes(global_ids, Product)

    assert exc.value.args == (msg,)
    global_ids.pop()

    # Raise an error if one of the node is of wrong type
    invalid_item = Mock(type="test", pk=-1)
    invalid_item_global_id = to_global_id(invalid_item.type, invalid_item.pk)
    global_ids.append(invalid_item_global_id)
    with pytest.raises(GraphQLError, match="Must receive Product id") as exc:
        get_nodes(global_ids, Product)

    assert exc.value.args == (f"Must receive Product id: {invalid_item_global_id}.",)

    # Raise an error if no nodes were found
    global_ids = []
    with pytest.raises(
        GraphQLError, match="Could not resolve to a node with the global id list of"
    ):
        get_nodes(global_ids, Product)

    # Raise an error if pass wrong ids
    global_ids = ["a", "bb"]
    with pytest.raises(
        GraphQLError, match="Could not resolve to a node with the global id list of"
    ):
        get_nodes(global_ids, Product)


def test_get_nodes_for_order_with_int_id(order_list):
    order_models.Order.objects.update(use_old_id=True)

    # given
    global_ids = [to_global_id("Order", order.number) for order in order_list]

    # Make sure function works even if duplicated ids are provided
    global_ids.append(to_global_id("Order", order_list[0].number))

    # when
    orders = get_nodes(global_ids, Order)

    # then
    assert orders == order_list


def test_get_nodes_for_order_with_uuid_id(order_list):
    # given
    global_ids = [to_global_id("Order", order.pk) for order in order_list]

    # Make sure function works even if duplicated ids are provided
    global_ids.append(to_global_id("Order", order_list[0].pk))

    # when
    orders = get_nodes(global_ids, Order)

    # then
    assert orders == order_list


def test_get_nodes_for_order_with_int_id_and_use_old_id_set_to_false(order_list):
    """Test that `get_node` respects `use_old_id`."""
    # given
    global_ids = [to_global_id("Order", order.number) for order in order_list]

    # Make sure function works even if duplicated ids are provided
    global_ids.append(to_global_id("Order", order_list[0].pk))

    # when
    with pytest.raises(AssertionError):
        get_nodes(global_ids, Order)


def test_get_nodes_for_order_with_uuid_and_int_id(order_list):
    """Test that `get_nodes` works for both old and new order IDs."""
    # given
    order_models.Order.objects.update(use_old_id=True)
    global_ids = [to_global_id("Order", order.pk) for order in order_list[:-1]]
    global_ids.append(to_global_id("Order", order_list[-1].number))

    # when
    orders = get_nodes(global_ids, Order)

    # then
    assert orders == order_list


def test_from_global_id_or_error(product):
    invalid_id = "invalid"
    message = f"Invalid ID: {invalid_id}."

    with pytest.raises(GraphQLError) as error:
        from_global_id_or_error(invalid_id)

    assert str(error.value) == message


def test_from_global_id_or_error_wth_invalid_type(product):
    product_id = graphene.Node.to_global_id("Product", product.id)
    message = f"Invalid ID: {product_id}. Expected: ProductVariant, received: Product."

    with pytest.raises(GraphQLError) as error:
        from_global_id_or_error(product_id, "ProductVariant", raise_error=True)

    assert str(error.value) == message


def test_from_global_id_or_error_wth_type(product):
    expected_product_type = str(Product)
    expected_product_id = graphene.Node.to_global_id(expected_product_type, product.id)

    product_type, product_id = from_global_id_or_error(
        expected_product_id, expected_product_type
    )

    assert product_id == str(product.id)
    assert product_type == expected_product_type


@mock.patch("saleor.graphql.order.schema.create_connection_slice")
def test_query_allow_replica(
    mocked_resolver, staff_api_client, order, permission_manage_orders
):
    # given
    query = """
        query {
          orders(first: 5){
            edges {
              node {
                id
              }
            }
          }
        }
    """

    # when
    staff_api_client.post_graphql(query, permissions=[permission_manage_orders])

    # then
    assert mocked_resolver.call_args[0][1].context.allow_replica
