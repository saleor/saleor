import pytest

from .....product import ProductTypeKind
from .....product.models import ProductType
from ....tests.utils import get_graphql_content


def test_product_types(user_api_client, product_type, channel_USD):
    query = """
    query ($channel: String){
        productTypes(first: 20) {
            totalCount
            edges {
                node {
                    id
                    name
                    products(first: 1, channel: $channel) {
                        edges {
                            node {
                                id
                            }
                        }
                    }
                }
            }
        }
    }
    """
    variables = {"channel": channel_USD.slug}
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    no_product_types = ProductType.objects.count()
    assert content["data"]["productTypes"]["totalCount"] == no_product_types
    assert len(content["data"]["productTypes"]["edges"]) == no_product_types


@pytest.mark.parametrize(
    "product_type_filter, count",
    [
        ({"configurable": "CONFIGURABLE"}, 2),  # has_variants
        ({"configurable": "SIMPLE"}, 1),  # !has_variants
        ({"productType": "DIGITAL"}, 1),
        ({"productType": "SHIPPABLE"}, 2),  # is_shipping_required
        ({"kind": "NORMAL"}, 2),
        ({"kind": "GIFT_CARD"}, 1),
        ({"slugs": ["digital-type", "tools"]}, 2),
        ({"slugs": []}, 3),
    ],
)
def test_product_type_query_with_filter(
    product_type_filter, count, staff_api_client, permission_manage_products
):
    query = """
        query ($filter: ProductTypeFilterInput!, ) {
          productTypes(first:5, filter: $filter) {
            edges{
              node{
                id
                name
              }
            }
          }
        }
        """
    ProductType.objects.bulk_create(
        [
            ProductType(
                name="Digital Type",
                slug="digital-type",
                has_variants=True,
                is_shipping_required=False,
                is_digital=True,
                kind=ProductTypeKind.NORMAL,
            ),
            ProductType(
                name="Tools",
                slug="tools",
                has_variants=True,
                is_shipping_required=True,
                is_digital=False,
                kind=ProductTypeKind.NORMAL,
            ),
            ProductType(
                name="Books",
                slug="books",
                has_variants=False,
                is_shipping_required=True,
                is_digital=False,
                kind=ProductTypeKind.GIFT_CARD,
            ),
        ]
    )

    variables = {"filter": product_type_filter}
    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    product_types = content["data"]["productTypes"]["edges"]

    assert len(product_types) == count


QUERY_PRODUCT_TYPES_WITH_SORT = """
    query ($sort_by: ProductTypeSortingInput!) {
        productTypes(first:5, sortBy: $sort_by) {
                edges{
                    node{
                        name
                    }
                }
            }
        }
"""


@pytest.mark.parametrize(
    "product_type_sort, result_order",
    [
        ({"field": "NAME", "direction": "ASC"}, ["Digital", "Subscription", "Tools"]),
        ({"field": "NAME", "direction": "DESC"}, ["Tools", "Subscription", "Digital"]),
        # is_digital
        (
            {"field": "DIGITAL", "direction": "ASC"},
            ["Subscription", "Tools", "Digital"],
        ),
        (
            {"field": "DIGITAL", "direction": "DESC"},
            ["Digital", "Tools", "Subscription"],
        ),
        # is_shipping_required
        (
            {"field": "SHIPPING_REQUIRED", "direction": "ASC"},
            ["Digital", "Subscription", "Tools"],
        ),
        (
            {"field": "SHIPPING_REQUIRED", "direction": "DESC"},
            ["Tools", "Subscription", "Digital"],
        ),
    ],
)
def test_product_type_query_with_sort(
    product_type_sort, result_order, staff_api_client, permission_manage_products
):
    ProductType.objects.bulk_create(
        [
            ProductType(
                name="Digital",
                slug="digital",
                has_variants=True,
                is_shipping_required=False,
                is_digital=True,
            ),
            ProductType(
                name="Tools",
                slug="tools",
                has_variants=True,
                is_shipping_required=True,
                is_digital=False,
            ),
            ProductType(
                name="Subscription",
                slug="subscription",
                has_variants=False,
                is_shipping_required=False,
                is_digital=False,
            ),
        ]
    )

    variables = {"sort_by": product_type_sort}
    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(QUERY_PRODUCT_TYPES_WITH_SORT, variables)
    content = get_graphql_content(response)
    product_types = content["data"]["productTypes"]["edges"]

    for order, product_type_name in enumerate(result_order):
        assert product_types[order]["node"]["name"] == product_type_name


NOT_EXISTS_IDS_COLLECTIONS_QUERY = """
    query ($filter: ProductTypeFilterInput!) {
        productTypes(first: 5, filter: $filter) {
            edges {
                node {
                    id
                    name
                }
            }
        }
    }
"""


def test_product_types_query_ids_not_exists(user_api_client, category):
    query = NOT_EXISTS_IDS_COLLECTIONS_QUERY
    variables = {"filter": {"ids": ["fTEJRuFHU6fd2RU=", "2XwnQNNhwCdEjhP="]}}
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response, ignore_errors=True)
    message_error = '{"ids": [{"message": "Invalid ID specified.", "code": ""}]}'

    assert len(content["errors"]) == 1
    assert content["errors"][0]["message"] == message_error
    assert content["data"]["productTypes"] is None


QUERY_FILTER_PRODUCT_TYPES = """
    query($filters: ProductTypeFilterInput) {
      productTypes(first: 10, filter: $filters) {
        edges {
          node {
            name
          }
        }
      }
    }
"""


@pytest.mark.parametrize(
    "search, expected_names",
    (
        ("", ["The best juices", "The best beers", "The worst beers"]),
        ("best", ["The best juices", "The best beers"]),
        ("worst", ["The worst beers"]),
        ("average", []),
    ),
)
def test_filter_product_types_by_custom_search_value(
    api_client, search, expected_names
):
    query = QUERY_FILTER_PRODUCT_TYPES

    ProductType.objects.bulk_create(
        [
            ProductType(name="The best juices", slug="best-juices"),
            ProductType(name="The best beers", slug="best-beers"),
            ProductType(name="The worst beers", slug="worst-beers"),
        ]
    )

    variables = {"filters": {"search": search}}

    results = get_graphql_content(api_client.post_graphql(query, variables))["data"][
        "productTypes"
    ]["edges"]

    assert len(results) == len(expected_names)
    matched_names = sorted([result["node"]["name"] for result in results])

    assert matched_names == sorted(expected_names)
