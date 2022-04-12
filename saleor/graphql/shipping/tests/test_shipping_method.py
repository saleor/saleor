import graphene
import pytest

from ...tests.utils import get_graphql_content

EXCLUDE_PRODUCTS_MUTATION = """
    mutation shippingPriceRemoveProductFromExclude(
        $id: ID!, $input:ShippingPriceExcludeProductsInput!
        ) {
        shippingPriceExcludeProducts(
            id: $id
            input: $input) {
            errors {
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


@pytest.mark.parametrize("requestor", ["staff", "app"])
def test_exclude_products_for_shipping_method_only_products(
    requestor,
    app_api_client,
    shipping_method,
    product_list,
    staff_api_client,
    permission_manage_shipping,
):
    api = staff_api_client if requestor == "staff" else app_api_client
    shipping_method_id = graphene.Node.to_global_id(
        "ShippingMethodType", shipping_method.pk
    )
    product_ids = [graphene.Node.to_global_id("Product", p.pk) for p in product_list]
    variables = {"id": shipping_method_id, "input": {"products": product_ids}}
    response = api.post_graphql(
        EXCLUDE_PRODUCTS_MUTATION, variables, permissions=[permission_manage_shipping]
    )
    content = get_graphql_content(response)
    shipping_method = content["data"]["shippingPriceExcludeProducts"]["shippingMethod"]
    excluded_products = shipping_method["excludedProducts"]
    total_count = excluded_products["totalCount"]
    excluded_product_ids = {p["node"]["id"] for p in excluded_products["edges"]}
    assert len(product_ids) == total_count
    assert excluded_product_ids == set(product_ids)


@pytest.mark.parametrize("requestor", ["staff", "app"])
def test_exclude_products_for_shipping_method_already_has_excluded_products(
    requestor,
    shipping_method,
    product_list,
    product,
    staff_api_client,
    permission_manage_shipping,
    app_api_client,
):
    api = staff_api_client if requestor == "staff" else app_api_client
    shipping_method_id = graphene.Node.to_global_id(
        "ShippingMethodType", shipping_method.pk
    )
    shipping_method.excluded_products.add(product, product_list[0])
    product_ids = [graphene.Node.to_global_id("Product", p.pk) for p in product_list]
    variables = {"id": shipping_method_id, "input": {"products": product_ids}}
    response = api.post_graphql(
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
        $id: ID!, $products: [ID!]!
        ) {
        shippingPriceRemoveProductFromExclude(
            id: $id
            products: $products) {
            errors {
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


@pytest.mark.parametrize("requestor", ["staff", "app"])
def test_remove_products_from_excluded_products_for_shipping_method_delete_all_products(
    requestor,
    shipping_method,
    product_list,
    staff_api_client,
    permission_manage_shipping,
    app_api_client,
):
    api = staff_api_client if requestor == "staff" else app_api_client
    shipping_method_id = graphene.Node.to_global_id(
        "ShippingMethodType", shipping_method.pk
    )
    shipping_method.excluded_products.set(product_list)

    product_ids = [graphene.Node.to_global_id("Product", p.pk) for p in product_list]
    variables = {"id": shipping_method_id, "products": product_ids}
    response = api.post_graphql(
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
    excluded_product_ids = {p["node"]["id"] for p in excluded_products["edges"]}
    assert total_count == 0
    assert len(excluded_product_ids) == 0


@pytest.mark.parametrize("requestor", ["staff", "app"])
def test_remove_products_from_excluded_products_for_shipping_method(
    requestor,
    shipping_method,
    product_list,
    staff_api_client,
    permission_manage_shipping,
    product,
    app_api_client,
):
    api = staff_api_client if requestor == "staff" else app_api_client
    shipping_method_id = graphene.Node.to_global_id(
        "ShippingMethodType", shipping_method.pk
    )
    shipping_method.excluded_products.set(product_list)
    shipping_method.excluded_products.add(product)

    product_ids = [
        graphene.Node.to_global_id("Product", product.pk),
    ]
    variables = {"id": shipping_method_id, "products": product_ids}
    response = api.post_graphql(
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
