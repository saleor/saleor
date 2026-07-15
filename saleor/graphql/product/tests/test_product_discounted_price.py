from unittest.mock import patch

from graphql_relay import to_global_id

from ....discount.utils.promotion import get_active_catalogue_promotion_rules
from ...tests.utils import get_graphql_content


@patch("saleor.order.tasks.recalculate_orders_task.delay")
def test_product_variant_delete_updates_discounted_price(
    mocked_recalculate_orders_task,
    staff_api_client,
    product,
    permission_manage_products,
):
    # given
    query = """
        mutation ProductVariantDelete($id: ID!) {
            productVariantDelete(id: $id) {
                productVariant {
                    id
                }
                errors {
                    field
                    message
                }
              }
            }
    """
    variant = product.variants.first()
    variant_id = to_global_id("ProductVariant", variant.pk)
    variables = {"id": variant_id}

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["productVariantDelete"]
    assert data["errors"] == []
    for rule in get_active_catalogue_promotion_rules():
        assert rule.variants_dirty
    mocked_recalculate_orders_task.assert_not_called()


def test_category_delete_updates_discounted_price(
    staff_api_client,
    categories_tree_with_published_products,
    permission_manage_products,
):
    # given
    parent = categories_tree_with_published_products
    product_list = [parent.children.first().products.first(), parent.products.first()]

    query = """
        mutation CategoryDelete($id: ID!) {
            categoryDelete(id: $id) {
                category {
                    name
                }
                errors {
                    field
                    message
                }
            }
        }
    """
    variables = {"id": to_global_id("Category", parent.pk)}

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )

    # then
    assert response.status_code == 200

    content = get_graphql_content(response)
    data = content["data"]["categoryDelete"]
    assert data["errors"] == []

    for rule in get_active_catalogue_promotion_rules():
        assert rule.variants_dirty

    for product in product_list:
        product.refresh_from_db()
        assert not product.category


def test_collection_add_products_updates_rule_variants_dirty(
    staff_api_client,
    collection,
    product_list,
    permission_manage_products,
):
    # given
    assert collection.products.count() == 0
    query = """
        mutation CollectionAddProducts($id: ID!, $products: [ID!]!) {
            collectionAddProducts(collectionId: $id, products: $products) {
                collection {
                    products {
                        totalCount
                    }
                }
                errors {
                    field
                    message
                }
            }
        }
    """
    collection_id = to_global_id("Collection", collection.id)
    product_ids = [to_global_id("Product", product.pk) for product in product_list]
    variables = {"id": collection_id, "products": product_ids}

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["collectionAddProducts"]
    assert data["errors"] == []
    for rule in get_active_catalogue_promotion_rules():
        assert rule.variants_dirty


def test_collection_remove_products_updates_rule_variants_dirty(
    staff_api_client,
    collection,
    product_list,
    permission_manage_products,
):
    # given
    assert collection.products.count() == 0
    query = """
        mutation CollectionRemoveProducts($id: ID!, $products: [ID!]!) {
            collectionRemoveProducts(collectionId: $id, products: $products) {
                collection {
                    products {
                        totalCount
                    }
                }
                errors {
                    field
                    message
                }
            }
        }
    """
    collection_id = to_global_id("Collection", collection.id)
    product_ids = [to_global_id("Product", product.pk) for product in product_list]
    variables = {"id": collection_id, "products": product_ids}

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["collectionRemoveProducts"]
    assert data["errors"] == []
    for rule in get_active_catalogue_promotion_rules():
        assert rule.variants_dirty
