from unittest.mock import patch

import graphene

from .....discount.utils.promotion import get_active_catalogue_promotion_rules
from ....tests.utils import (
    get_graphql_content,
)

COLLECTION_REMOVE_PRODUCTS_MUTATION = """
    mutation collectionRemoveProducts(
        $id: ID!, $products: [ID!]!) {
        collectionRemoveProducts(collectionId: $id, products: $products) {
            collection {
                products {
                    totalCount
                }
            }
        }
    }
"""


def test_remove_products_from_collection(
    staff_api_client,
    collection,
    product_list,
    permission_manage_products,
):
    # given
    query = COLLECTION_REMOVE_PRODUCTS_MUTATION
    collection.products.add(*product_list)
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
    data = content["data"]["collectionRemoveProducts"]["collection"]
    assert data["products"]["totalCount"] == products_before - len(product_ids)
    for rule in get_active_catalogue_promotion_rules():
        assert rule.variants_dirty is True


@patch("saleor.plugins.manager.PluginsManager.product_updated")
def test_remove_products_from_collection_trigger_product_updated_webhook(
    product_updated_mock,
    staff_api_client,
    collection,
    product_list,
    permission_manage_products,
):
    query = COLLECTION_REMOVE_PRODUCTS_MUTATION
    collection.products.add(*product_list)
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
    data = content["data"]["collectionRemoveProducts"]["collection"]
    assert data["products"]["totalCount"] == products_before - len(product_ids)
    assert len(product_list) == product_updated_mock.call_count
