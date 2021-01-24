import graphene
import pytest

from ....tests.utils import get_graphql_content

SHIPPING_METHODS_QUERY = """
query GetShippingMethods($channel: String) {
  shippingZones(first: 10, channel: $channel) {
    edges {
      node {
        shippingMethods {
          id
          name
          minimumOrderWeight {
            unit
            value
          }
          maximumOrderWeight {
            unit
            value
          }
          type
          channelListings {
            id
            channel {
              id
              name
            }
          }
          price {
            amount
            currency
          }
          maximumOrderPrice {
            currency
            amount
          }
          minimumOrderPrice {
            currency
            amount
          }
        }
      }
    }
  }
}
"""


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_vouchers_query_with_channel_slug(
    staff_api_client,
    shipping_zones,
    channel_USD,
    permission_manage_shipping,
    count_queries,
):
    variables = {"channel": channel_USD.slug}
    get_graphql_content(
        staff_api_client.post_graphql(
            SHIPPING_METHODS_QUERY,
            variables,
            permissions=[permission_manage_shipping],
            check_no_permissions=False,
        )
    )


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_vouchers_query_without_channel_slug(
    staff_api_client,
    shipping_zones,
    permission_manage_shipping,
    count_queries,
):
    get_graphql_content(
        staff_api_client.post_graphql(
            SHIPPING_METHODS_QUERY,
            {},
            permissions=[permission_manage_shipping],
            check_no_permissions=False,
        )
    )


EXCLUDE_PRODUCTS_MUTATION = """
    mutation shippingPriceRemoveProductFromExclude(
        $id: ID!, $input:ShippingPriceExcludeProductsInput!
        ) {
        shippingPriceExcludeProducts(
            id: $id
            input: $input) {
            shippingErrors {
                field
                code
            }
            shippingMethod {
                id
                excludedProducts(first:10){
                   totalCount
                   edges{
                     node{
                       id
                     }
                   }
                }
            }
        }
    }
"""


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_exclude_products_for_shipping_method(
    shipping_method,
    published_collection,
    product_list_published,
    product_list,
    categories_tree_with_published_products,
    collection,
    staff_api_client,
    permission_manage_shipping,
):
    # product_list has products with slugs slug:test-product-a, slug:test-product-b,
    # slug:test-product-c
    product_db_ids = [p.pk for p in product_list]
    product_ids = [graphene.Node.to_global_id("Product", p) for p in product_db_ids]

    expected_product_ids = [
        graphene.Node.to_global_id("Product", p.pk) for p in product_list
    ]

    shipping_method_id = graphene.Node.to_global_id(
        "ShippingMethod", shipping_method.pk
    )
    variables = {
        "id": shipping_method_id,
        "input": {"products": product_ids},
    }

    response = staff_api_client.post_graphql(
        EXCLUDE_PRODUCTS_MUTATION, variables, permissions=[permission_manage_shipping]
    )

    content = get_graphql_content(response)
    shipping_method = content["data"]["shippingPriceExcludeProducts"]["shippingMethod"]
    excluded_products = shipping_method["excludedProducts"]
    total_count = excluded_products["totalCount"]
    excluded_product_ids = {p["node"]["id"] for p in excluded_products["edges"]}
    assert len(expected_product_ids) == total_count == 3
    assert excluded_product_ids == set(expected_product_ids)


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_exclude_products_for_shipping_method_already_has_excluded_products(
    shipping_method,
    product_list,
    product,
    staff_api_client,
    permission_manage_shipping,
):
    shipping_method_id = graphene.Node.to_global_id(
        "ShippingMethod", shipping_method.pk
    )
    shipping_method.excluded_products.add(product, product_list[0])
    product_ids = [graphene.Node.to_global_id("Product", p.pk) for p in product_list]
    variables = {"id": shipping_method_id, "input": {"products": product_ids}}
    response = staff_api_client.post_graphql(
        EXCLUDE_PRODUCTS_MUTATION, variables, permissions=[permission_manage_shipping]
    )
    content = get_graphql_content(response)
    shipping_method = content["data"]["shippingPriceExcludeProducts"]["shippingMethod"]
    excluded_products = shipping_method["excludedProducts"]
    total_count = excluded_products["totalCount"]
    expected_product_ids = product_ids
    expected_product_ids.append(graphene.Node.to_global_id("Product", product.pk))
    excluded_product_ids = {p["node"]["id"] for p in excluded_products["edges"]}
    assert len(expected_product_ids) == total_count
    assert excluded_product_ids == set(expected_product_ids)


REMOVE_PRODUCTS_FROM_EXCLUDED_PRODUCTS_MUTATION = """
    mutation shippingPriceRemoveProductFromExclude(
        $id: ID!, $products: [ID]!
        ) {
        shippingPriceRemoveProductFromExclude(
            id: $id
            products: $products) {
            shippingErrors {
                field
                code
            }
            shippingMethod {
                id
                excludedProducts(first:10){
                   totalCount
                   edges{
                     node{
                       id
                     }
                   }
                }
            }
        }
    }
"""


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_remove_products_from_excluded_products_for_shipping_method(
    shipping_method,
    product_list,
    staff_api_client,
    permission_manage_shipping,
    product,
):
    shipping_method_id = graphene.Node.to_global_id(
        "ShippingMethod", shipping_method.pk
    )
    shipping_method.excluded_products.set(product_list)
    shipping_method.excluded_products.add(product)

    product_ids = [
        graphene.Node.to_global_id("Product", product.pk),
    ]
    variables = {"id": shipping_method_id, "products": product_ids}
    response = staff_api_client.post_graphql(
        REMOVE_PRODUCTS_FROM_EXCLUDED_PRODUCTS_MUTATION,
        variables,
        permissions=[permission_manage_shipping],
    )

    content = get_graphql_content(response)
    shipping_method = content["data"]["shippingPriceRemoveProductFromExclude"][
        "shippingMethod"
    ]
    excluded_products = shipping_method["excludedProducts"]
    total_count = excluded_products["totalCount"]
    expected_product_ids = {
        graphene.Node.to_global_id("Product", p.pk) for p in product_list
    }
    excluded_product_ids = {p["node"]["id"] for p in excluded_products["edges"]}
    assert total_count == len(expected_product_ids)
    assert excluded_product_ids == expected_product_ids
