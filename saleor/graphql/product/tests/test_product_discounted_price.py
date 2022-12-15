from unittest.mock import patch

from freezegun import freeze_time
from graphql_relay import from_global_id, to_global_id

from ...discount.enums import DiscountValueTypeEnum
from ...tests.utils import get_graphql_content


@patch(
    "saleor.graphql.product.mutations.product_variant.product_variant_delete"
    ".update_product_discounted_price_task"
)
@patch("saleor.order.tasks.recalculate_orders_task.delay")
def test_product_variant_delete_updates_discounted_price(
    mocked_recalculate_orders_task,
    mock_update_product_discounted_price_task,
    staff_api_client,
    product,
    permission_manage_products,
):
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
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["productVariantDelete"]
    assert data["errors"] == []

    mock_update_product_discounted_price_task.delay.assert_called_once_with(product.pk)
    mocked_recalculate_orders_task.assert_not_called()


@patch("saleor.product.utils.update_products_discounted_prices_task")
def test_category_delete_updates_discounted_price(
    mock_update_products_discounted_prices_task,
    staff_api_client,
    categories_tree_with_published_products,
    permission_manage_products,
):
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
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    assert response.status_code == 200

    content = get_graphql_content(response)
    data = content["data"]["categoryDelete"]
    assert data["errors"] == []

    mock_update_products_discounted_prices_task.delay.assert_called_once()
    (
        _call_args,
        call_kwargs,
    ) = mock_update_products_discounted_prices_task.delay.call_args
    assert set(call_kwargs["product_ids"]) == set(p.pk for p in product_list)

    for product in product_list:
        product.refresh_from_db()
        assert not product.category


@patch(
    "saleor.graphql.product.mutations.collection.collection_add_products"
    ".update_products_discounted_prices_of_catalogues_task"
)
def test_collection_add_products_updates_discounted_price(
    mock_update_products_discounted_prices_of_catalogues,
    staff_api_client,
    sale,
    collection,
    product_list,
    permission_manage_products,
):
    sale.collections.add(collection)
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
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["collectionAddProducts"]
    assert data["errors"] == []

    mock_update_products_discounted_prices_of_catalogues.delay.assert_called_once_with(
        product_ids=[p.pk for p in product_list]
    )


@patch(
    "saleor.graphql.product.mutations.collection.collection_remove_products"
    ".update_products_discounted_prices_of_catalogues_task"
)
def test_collection_remove_products_updates_discounted_price(
    mock_update_products_discounted_prices_of_catalogues,
    staff_api_client,
    sale,
    collection,
    product_list,
    permission_manage_products,
):
    sale.collections.add(collection)
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
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["collectionRemoveProducts"]
    assert data["errors"] == []

    mock_update_products_discounted_prices_of_catalogues.delay.assert_called_once_with(
        product_ids=[p.pk for p in product_list]
    )


@freeze_time("2010-05-31 12:00:01")
@patch(
    "saleor.graphql.discount.mutations.sale_create"
    ".update_products_discounted_prices_of_discount_task"
)
def test_sale_create_updates_products_discounted_prices(
    mock_update_products_discounted_prices_of_catalogues,
    staff_api_client,
    permission_manage_discounts,
):
    query = """
    mutation SaleCreate(
            $name: String,
            $type: DiscountValueTypeEnum,
            $value: PositiveDecimal,
            $products: [ID!]
    ) {
        saleCreate(input: {
                name: $name,
                type: $type,
                value: $value,
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
        "value": "50",
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_discounts]
    )
    assert response.status_code == 200

    content = get_graphql_content(response)
    assert content["data"]["saleCreate"]["errors"] == []

    relay_sale_id = content["data"]["saleCreate"]["sale"]["id"]
    _sale_class_name, sale_id_str = from_global_id(relay_sale_id)
    sale_id = int(sale_id_str)
    mock_update_products_discounted_prices_of_catalogues.delay.assert_called_once_with(
        sale_id
    )


@patch(
    "saleor.graphql.discount.mutations.sale_create"
    ".update_products_discounted_prices_of_discount_task"
)
def test_sale_update_updates_products_discounted_prices(
    mock_update_products_discounted_prices_of_discount,
    staff_api_client,
    sale,
    permission_manage_discounts,
):
    query = """
    mutation SaleUpdate($id: ID!, $value: PositiveDecimal) {
        saleUpdate(id: $id, input: {value: $value}) {
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
    variables = {"id": to_global_id("Sale", sale.pk), "value": "99"}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_discounts]
    )
    assert response.status_code == 200

    content = get_graphql_content(response)
    assert content["data"]["saleUpdate"]["errors"] == []

    mock_update_products_discounted_prices_of_discount.delay.assert_called_once_with(
        sale.pk
    )


@patch(
    "saleor.graphql.discount.mutations.sale_create"
    ".update_products_discounted_prices_of_discount_task"
)
def test_sale_delete_updates_products_discounted_prices(
    mock_update_products_discounted_prices_of_discount,
    staff_api_client,
    sale,
    permission_manage_discounts,
):
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
    variables = {"id": to_global_id("Sale", sale.pk)}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_discounts]
    )
    assert response.status_code == 200

    content = get_graphql_content(response)
    assert content["data"]["saleDelete"]["errors"] == []

    mock_update_products_discounted_prices_of_discount.delay.assert_called_once_with(
        sale.pk
    )


@patch(
    "saleor.graphql.discount.mutations.sale_base_discount_catalogue"
    ".update_products_discounted_prices_of_catalogues_task"
)
def test_sale_add_catalogues_updates_products_discounted_prices(
    mock_update_products_discounted_prices_of_catalogues,
    staff_api_client,
    sale,
    product,
    category,
    collection,
    product_variant_list,
    permission_manage_discounts,
):
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
    sale_id = to_global_id("Sale", sale.pk)
    product_id = to_global_id("Product", product.pk)
    collection_id = to_global_id("Collection", collection.pk)
    category_id = to_global_id("Category", category.pk)
    variant_ids = [
        to_global_id("ProductVariant", variant.pk) for variant in product_variant_list
    ]
    variables = {
        "id": sale_id,
        "input": {
            "products": [product_id],
            "collections": [collection_id],
            "categories": [category_id],
            "variants": variant_ids,
        },
    }

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_discounts]
    )
    assert response.status_code == 200

    content = get_graphql_content(response)
    assert not content["data"]["saleCataloguesAdd"]["errors"]

    mock_update_products_discounted_prices_of_catalogues.delay.assert_called_once_with(
        product_ids=[product.pk],
        category_ids=[category.pk],
        collection_ids=[collection.pk],
        variant_ids=[variant.pk for variant in product_variant_list],
    )


@patch(
    "saleor.graphql.discount.mutations.sale_base_discount_catalogue"
    ".update_products_discounted_prices_of_catalogues_task"
)
def test_sale_remove_catalogues_updates_products_discounted_prices(
    mock_update_products_discounted_prices_of_catalogues,
    staff_api_client,
    sale,
    product,
    category,
    collection,
    product_variant_list,
    permission_manage_discounts,
):
    assert product in sale.products.all()
    assert category in sale.categories.all()
    assert collection in sale.collections.all()

    sale.variants.add(*product_variant_list)

    assert all(variant in sale.variants.all() for variant in product_variant_list)
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
    sale_id = to_global_id("Sale", sale.pk)
    product_id = to_global_id("Product", product.pk)
    collection_id = to_global_id("Collection", collection.pk)
    category_id = to_global_id("Category", category.pk)
    variant_ids = [
        to_global_id("ProductVariant", variant.pk) for variant in product_variant_list
    ]
    variables = {
        "id": sale_id,
        "input": {
            "products": [product_id],
            "collections": [collection_id],
            "categories": [category_id],
            "variants": variant_ids,
        },
    }

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_discounts]
    )
    assert response.status_code == 200

    content = get_graphql_content(response)
    assert not content["data"]["saleCataloguesRemove"]["errors"]

    mock_update_products_discounted_prices_of_catalogues.delay.assert_called_once_with(
        product_ids=[product.pk],
        category_ids=[category.pk],
        collection_ids=[collection.pk],
        variant_ids=[variant.pk for variant in product_variant_list],
    )
