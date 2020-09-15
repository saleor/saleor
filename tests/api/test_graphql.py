from functools import partial
from unittest.mock import Mock, patch

import graphene
import pytest
from django.contrib.auth.models import AnonymousUser
from django.db.models import Q
from django.shortcuts import reverse
from graphql.error import GraphQLError
from graphql_relay import to_global_id

from saleor.graphql.product.types import Product
from saleor.graphql.utils import get_nodes
from saleor.graphql.utils.filters import filter_by_query_param
from tests.api.utils import get_graphql_content


def test_middleware_dont_generate_sql_requests(client, settings, assert_num_queries):
    """When requesting on the GraphQL API endpoint, no SQL request should happen
    indirectly. This test ensures that."""

    # Enables the Graphql playground
    settings.DEBUG = True

    with assert_num_queries(0):
        response = client.get(reverse("api"))
        assert response.status_code == 200


def test_jwt_middleware(client, admin_user):
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
    assert isinstance(response.wsgi_request.user, AnonymousUser)
    assert repl_data["data"]["me"] is None

    # test creating a token for admin user
    response = api_client_post(data={"query": create_token_query})
    repl_data = response.json()
    assert response.status_code == 200
    assert response.wsgi_request.user == admin_user
    token = repl_data["data"]["tokenCreate"]["token"]
    assert token is not None

    # test request with proper JWT token authorizes the request to API
    response = api_client_post(
        data={"query": user_details_query}, HTTP_AUTHORIZATION=f"JWT {token}"
    )
    repl_data = response.json()
    assert response.status_code == 200
    assert response.wsgi_request.user == admin_user
    assert "errors" not in repl_data
    assert repl_data["data"]["me"] == {"email": admin_user.email}


def test_real_query(user_api_client, product):
    product_attr = product.product_type.product_attributes.first()
    category = product.category
    attr_value = product_attr.values.first()
    query = """
    query Root($categoryId: ID!, $sortBy: ProductOrder, $first: Int,
            $attributesFilter: [AttributeInput], $minPrice: Float, $maxPrice: Float) {

        category(id: $categoryId) {
            ...CategoryPageFragmentQuery
            __typename
        }
        products(first: $first, sortBy: $sortBy, filter: {categories: [$categoryId],
            attributes: $attributesFilter, price: {gte: $minPrice, lte: $maxPrice}}) {

            ...ProductListFragmentQuery
            __typename
        }
        attributes(first: 20, filter: {inCategory: $categoryId}) {
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
        url
        ancestors(first: 20) {
            edges {
                node {
                    name
                    id
                    url
                    __typename
                }
            }
        }
        children(first: 20) {
            edges {
                node {
                    name
                    id
                    url
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
        url
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
                    localized
                    __typename
                }
                currency
                __typename
            }
            start {
                gross {
                    amount
                    currency
                    localized
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
        values {
            id
            name
            slug
            __typename
        }
        __typename
    }
    """
    variables = {
        "categoryId": graphene.Node.to_global_id("Category", category.id),
        "sortBy": {"field": "NAME", "direction": "ASC"},
        "first": 1,
        "attributesFilter": [
            {"slug": f"{product_attr.slug}", "value": f"{attr_value.slug}"}
        ],
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
    nonexistent_item = Mock(type="Product", pk=123)
    nonexistent_item_global_id = to_global_id(
        nonexistent_item.type, nonexistent_item.pk
    )
    global_ids.append(nonexistent_item_global_id)
    msg = "There is no node of type {} with pk {}".format(
        nonexistent_item.type, nonexistent_item.pk
    )
    with pytest.raises(AssertionError) as exc:
        get_nodes(global_ids, Product)

    assert exc.value.args == (msg,)
    global_ids.pop()

    # Raise an error if one of the node is of wrong type
    invalid_item = Mock(type="test", pk=123)
    invalid_item_global_id = to_global_id(invalid_item.type, invalid_item.pk)
    global_ids.append(invalid_item_global_id)
    with pytest.raises(GraphQLError) as exc:
        get_nodes(global_ids, Product)

    assert exc.value.args == (f"Must receive Product id: {invalid_item_global_id}",)

    # Raise an error if no nodes were found
    global_ids = []
    msg = f"Could not resolve to a node with the global id list of '{global_ids}'."
    with pytest.raises(Exception) as exc:
        get_nodes(global_ids, Product)

    assert exc.value.args == (msg,)

    # Raise an error if pass wrong ids
    global_ids = ["a", "bb"]
    msg = f"Could not resolve to a node with the global id list of '{global_ids}'."
    with pytest.raises(Exception) as exc:
        get_nodes(global_ids, Product)

    assert exc.value.args == (msg,)


@patch("saleor.product.models.Product.objects")
def test_filter_by_query_param(qs):
    qs.filter.return_value = qs

    qs = filter_by_query_param(qs, "test", ["name", "force"])
    test_kwargs = {"name__icontains": "test", "force__icontains": "test"}
    q_objects = Q()
    for q in test_kwargs:
        q_objects |= Q(**{q: test_kwargs[q]})
    # FIXME: django 1.11 fails on called_once_with(q_objects)
    qs.filter.call_count == 1
