from unittest.mock import patch

import graphene

from .....discount.utils.promotion import get_active_catalogue_promotion_rules
from .....product.error_codes import CollectionErrorCode
from ....tests.utils import (
    get_graphql_content,
)

COLLECTION_ADD_PRODUCTS_MUTATION = """
    mutation collectionAddProducts(
        $id: ID!, $products: [ID!]!) {
        collectionAddProducts(collectionId: $id, products: $products) {
            collection {
                products {
                    totalCount
                }
            }
            errors {
                field
                message
                code
            }
        }
    }
"""


def test_add_products_to_collection(
    staff_api_client,
    collection,
    product_list,
    permission_manage_products,
):
    # given
    query = COLLECTION_ADD_PRODUCTS_MUTATION

    collection_id = graphene.Node.to_global_id("Collection", collection.id)
    product_ids = [
        graphene.Node.to_global_id("Product", product.pk) for product in product_list
    ]
    products_before = collection.products.count()
    variables = {"id": collection_id, "products": product_ids}

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["collectionAddProducts"]["collection"]
    assert data["products"]["totalCount"] == products_before + len(product_ids)
    for rule in get_active_catalogue_promotion_rules():
        assert rule.variants_dirty is True


@patch("saleor.plugins.manager.PluginsManager.product_updated")
def test_add_products_to_collection_trigger_product_updated_webhook(
    product_updated_mock,
    staff_api_client,
    collection,
    product_list,
    permission_manage_products,
):
    query = COLLECTION_ADD_PRODUCTS_MUTATION
    collection_id = graphene.Node.to_global_id("Collection", collection.id)
    product_ids = [
        graphene.Node.to_global_id("Product", product.pk) for product in product_list
    ]
    products_before = collection.products.count()
    variables = {"id": collection_id, "products": product_ids}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["collectionAddProducts"]["collection"]
    assert data["products"]["totalCount"] == products_before + len(product_ids)
    assert len(product_list) == product_updated_mock.call_count


def test_add_products_to_collection_on_sale_trigger_discounted_price_recalculation(
    staff_api_client, collection, product_list, permission_manage_products
):
    query = COLLECTION_ADD_PRODUCTS_MUTATION
    collection_id = graphene.Node.to_global_id("Collection", collection.id)
    product_ids = [
        graphene.Node.to_global_id("Product", product.pk) for product in product_list
    ]
    products_before = collection.products.count()
    variables = {"id": collection_id, "products": product_ids}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["collectionAddProducts"]["collection"]
    assert data["products"]["totalCount"] == products_before + len(product_ids)


def test_add_products_to_collection_with_product_without_variants(
    staff_api_client, collection, product_list, permission_manage_products
):
    query = COLLECTION_ADD_PRODUCTS_MUTATION
    product_list[0].variants.all().delete()
    collection_id = graphene.Node.to_global_id("Collection", collection.id)
    product_ids = [
        graphene.Node.to_global_id("Product", product.pk) for product in product_list
    ]
    variables = {"id": collection_id, "products": product_ids}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    error = content["data"]["collectionAddProducts"]["errors"][0]

    assert (
        error["code"] == CollectionErrorCode.CANNOT_MANAGE_PRODUCT_WITHOUT_VARIANT.name
    )
    assert error["message"] == "Cannot manage products without variants."
