from unittest.mock import patch

from freezegun import freeze_time
from graphql_relay import to_global_id

from ....discount.models import Promotion
from ...discount.enums import DiscountValueTypeEnum
from ...tests.utils import get_graphql_content


@patch(
    "saleor.graphql.product.mutations.product_variant.product_variant_delete"
    ".update_products_discounted_prices_for_promotion_task"
)
@patch("saleor.order.tasks.recalculate_orders_task.delay")
def test_product_variant_delete_updates_discounted_price(
    mocked_recalculate_orders_task,
    mock_update_products_discounted_prices_for_promotion_task,
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

    mock_update_products_discounted_prices_for_promotion_task.delay.assert_called_once_with(
        [product.pk]
    )
    mocked_recalculate_orders_task.assert_not_called()


@patch("saleor.product.utils.update_products_discounted_prices_for_promotion_task")
def test_category_delete_updates_discounted_price(
    mock_update_products_discounted_prices_for_promotion_task,
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

    mock_update_products_discounted_prices_for_promotion_task.delay.assert_called_once()
    (
        _call_args,
        call_kwargs,
    ) = mock_update_products_discounted_prices_for_promotion_task.delay.call_args
    assert set(call_kwargs["product_ids"]) == set(p.pk for p in product_list)

    for product in product_list:
        product.refresh_from_db()
        assert not product.category


@patch(
    "saleor.graphql.product.mutations.collection.collection_add_products"
    ".update_products_discounted_prices_for_promotion_task.delay"
)
def test_collection_add_products_updates_discounted_price(
    mock_update_products_discounted_prices_for_promotion_task,
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

    mock_update_products_discounted_prices_for_promotion_task.assert_called_once()
    args = set(
        mock_update_products_discounted_prices_for_promotion_task.call_args.args[0]
    )
    assert args == {product.id for product in product_list}


@patch(
    "saleor.graphql.product.mutations.collection.collection_remove_products"
    ".update_products_discounted_prices_for_promotion_task.delay"
)
def test_collection_remove_products_updates_discounted_price(
    mock_update_products_discounted_prices_for_promotion_task,
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

    mock_update_products_discounted_prices_for_promotion_task.assert_called_once()
    args = set(
        mock_update_products_discounted_prices_for_promotion_task.call_args.args[0]
    )
    assert args == {product.id for product in product_list}


@freeze_time("2010-05-31 12:00:01")
@patch(
    "saleor.graphql.discount.mutations.sale.sale_create"
    ".update_products_discounted_prices_of_promotion_task"
)
def test_sale_create_updates_products_discounted_prices(
    mock_update_products_discounted_prices_of_promotion_task,
    staff_api_client,
    permission_manage_discounts,
):
    # given
    query = """
    mutation SaleCreate(
            $name: String,
            $type: DiscountValueTypeEnum,
            $products: [ID!]
    ) {
        saleCreate(input: {
                name: $name,
                type: $type,
                products: $products
        }) {
            sale {
                id
            }
            errors {
                field
                message
            }
        }
    }
    """
    variables = {
        "name": "Half price product",
        "type": DiscountValueTypeEnum.PERCENTAGE.name,
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_discounts]
    )

    # then
    assert response.status_code == 200

    content = get_graphql_content(response)
    assert content["data"]["saleCreate"]["errors"] == []

    sale = Promotion.objects.filter(name="Half price product").get()
    mock_update_products_discounted_prices_of_promotion_task.delay.assert_called_once_with(
        sale.id
    )


@patch(
    "saleor.graphql.discount.mutations.sale.sale_update"
    ".update_products_discounted_prices_for_promotion_task"
)
def test_sale_update_updates_products_discounted_prices(
    mock_update_products_discounted_prices_for_promotion,
    staff_api_client,
    promotion_converted_from_sale,
    product,
    permission_manage_discounts,
):
    # given
    query = """
    mutation SaleUpdate($id: ID!, $type: DiscountValueTypeEnum) {
        saleUpdate(id: $id, input: {type: $type}) {
            sale {
                id
            }
            errors {
                field
                message
            }
        }
    }
    """
    promotion = promotion_converted_from_sale

    variables = {
        "id": to_global_id("Sale", promotion.old_sale_id),
        "type": DiscountValueTypeEnum.PERCENTAGE.name,
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_discounts]
    )

    # then
    assert response.status_code == 200
    content = get_graphql_content(response)
    assert content["data"]["saleUpdate"]["errors"] == []

    args, _ = mock_update_products_discounted_prices_for_promotion.delay.call_args
    assert args[0] == [product.id]


@patch(
    "saleor.graphql.discount.mutations.sale.sale_delete"
    ".update_products_discounted_prices_for_promotion_task"
)
def test_sale_delete_updates_products_discounted_prices(
    mock_update_products_discounted_prices_for_promotion,
    staff_api_client,
    promotion_converted_from_sale,
    product,
    permission_manage_discounts,
):
    # given
    query = """
    mutation SaleDelete($id: ID!) {
        saleDelete(id: $id) {
            sale {
                id
            }
            errors {
                field
                message
            }
        }
    }
    """
    promotion = promotion_converted_from_sale
    variables = {"id": to_global_id("Sale", promotion.old_sale_id)}

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_discounts]
    )

    # then
    assert response.status_code == 200

    content = get_graphql_content(response)
    assert content["data"]["saleDelete"]["errors"] == []

    args, _ = mock_update_products_discounted_prices_for_promotion.delay.call_args
    assert args[0] == [product.id]


@patch(
    "saleor.graphql.discount.mutations.sale.sale_base_catalogue"
    ".update_products_discounted_prices_for_promotion_task"
)
def test_sale_add_catalogues_updates_products_discounted_prices(
    mock_update_products_discounted_prices_for_promotion,
    staff_api_client,
    promotion_converted_from_sale_with_empty_predicate,
    product_list,
    permission_manage_discounts,
):
    # given
    query = """
        mutation SaleCataloguesAdd($id: ID!, $input: CatalogueInput!) {
            saleCataloguesAdd(id: $id, input: $input) {
                sale {
                    name
                }
                errors {
                    field
                    message
                }
            }
        }
    """
    promotion = promotion_converted_from_sale_with_empty_predicate
    sale_id = to_global_id("Sale", promotion.old_sale_id)
    product_ids = [to_global_id("Product", product.pk) for product in product_list]
    predicate = {"OR": [{"productPredicate": {"ids": [product_ids[0]]}}]}
    rule = promotion.rules.first()
    rule.catalogue_predicate = predicate
    rule.save(update_fields=["catalogue_predicate"])

    variables = {
        "id": sale_id,
        "input": {
            "products": product_ids[1:],
        },
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_discounts]
    )

    # then
    assert response.status_code == 200

    content = get_graphql_content(response)
    assert not content["data"]["saleCataloguesAdd"]["errors"]

    args, _ = mock_update_products_discounted_prices_for_promotion.delay.call_args
    assert set(args[0]) == {product.id for product in product_list[1:]}


@patch(
    "saleor.graphql.discount.mutations.sale.sale_base_catalogue"
    ".update_products_discounted_prices_for_promotion_task"
)
def test_sale_remove_catalogues_updates_products_discounted_prices(
    mock_update_products_discounted_prices_for_promotion,
    staff_api_client,
    promotion_converted_from_sale_with_empty_predicate,
    product_list,
    permission_manage_discounts,
):
    # given
    promotion = promotion_converted_from_sale_with_empty_predicate
    sale_id = to_global_id("Sale", promotion.old_sale_id)
    product_ids = [to_global_id("Product", product.pk) for product in product_list]
    predicate = {"OR": [{"productPredicate": {"ids": product_ids}}]}
    rule = promotion.rules.first()
    rule.catalogue_predicate = predicate
    rule.save(update_fields=["catalogue_predicate"])
    product_id = to_global_id("Product", product_list[-1].pk)

    query = """
        mutation SaleCataloguesRemove($id: ID!, $input: CatalogueInput!) {
            saleCataloguesRemove(id: $id, input: $input) {
                sale {
                    name
                }
                errors {
                    field
                    message
                }
            }
        }
    """

    variables = {
        "id": sale_id,
        "input": {
            "products": [product_id],
        },
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_discounts]
    )

    # then
    assert response.status_code == 200

    content = get_graphql_content(response)
    assert not content["data"]["saleCataloguesRemove"]["errors"]

    mock_update_products_discounted_prices_for_promotion.delay.called_once_with(
        product_id
    )
