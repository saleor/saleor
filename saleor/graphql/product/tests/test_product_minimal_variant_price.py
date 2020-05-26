from unittest.mock import patch

import graphene
from freezegun import freeze_time
from graphql_relay import from_global_id, to_global_id
from prices import Money

from saleor.graphql.discount.enums import DiscountValueTypeEnum
from saleor.product.error_codes import ProductErrorCode
from tests.api.utils import get_graphql_content


def test_product_create_sets_minimal_variant_price(
    staff_api_client, product_type, category, permission_manage_products
):
    query = """
        mutation ProductCreate(
            $name: String!,
            $productTypeId: ID!,
            $categoryId: ID!,
            $basePrice: Decimal!,
        ) {
            productCreate(
                input: {
                    name: $name,
                    productType: $productTypeId,
                    category: $categoryId,
                    basePrice: $basePrice
                }
            ) {
                product {
                    name
                    minimalVariantPrice {
                        amount
                    }
                }
                errors {
                    message
                    field
                }
            }
        }
    """
    product_name = "test name"
    product_type_id = to_global_id("ProductType", product_type.pk)
    category_id = to_global_id("Category", category.pk)
    product_price = "22.33"
    variables = {
        "name": product_name,
        "productTypeId": product_type_id,
        "categoryId": category_id,
        "basePrice": product_price,
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    assert response.status_code == 200

    content = get_graphql_content(response)
    data = content["data"]["productCreate"]
    assert data["errors"] == []
    assert str(data["product"]["minimalVariantPrice"]["amount"]) == product_price


@patch(
    "saleor.graphql.product.mutations.products"
    ".update_product_minimal_variant_price_task"
)
def test_product_update_updates_minimal_variant_price(
    mock_update_product_minimal_variant_price_task,
    staff_api_client,
    product,
    permission_manage_products,
):
    assert product.minimal_variant_price == Money("10.00", "USD")
    query = """
        mutation ProductUpdate(
            $productId: ID!,
            $basePrice: Decimal!,
        ) {
            productUpdate(
                id: $productId
                input: {
                    basePrice: $basePrice
                }
            ) {
                product {
                    name
                    minimalVariantPrice {
                        amount
                    }
                }
                errors {
                    message
                    field
                }
            }
        }
    """
    product_id = to_global_id("Product", product.pk)
    product_price = "1.99"
    variables = {"productId": product_id, "basePrice": product_price}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    assert response.status_code == 200

    content = get_graphql_content(response)
    data = content["data"]["productUpdate"]
    assert data["errors"] == []

    mock_update_product_minimal_variant_price_task.delay.assert_called_once_with(
        product.pk
    )


@patch(
    "saleor.graphql.product.mutations.products"
    ".update_product_minimal_variant_price_task"
)
def test_product_variant_create_updates_minimal_variant_price(
    mock_update_product_minimal_variant_price_task,
    staff_api_client,
    product,
    permission_manage_products,
):
    query = """
        mutation ProductVariantCreate(
            $productId: ID!,
            $sku: String!,
            $priceOverride: Decimal,
            $attributes: [AttributeValueInput]!,
        ) {
            productVariantCreate(
                input: {
                    product: $productId,
                    sku: $sku,
                    priceOverride: $priceOverride,
                    attributes: $attributes
                }
            ) {
                productVariant {
                    name
                }
                productErrors {
                    message
                    field
                }
            }
        }
    """
    product_id = to_global_id("Product", product.pk)
    sku = "1"
    price_override = "1.99"
    variant_id = graphene.Node.to_global_id(
        "Attribute", product.product_type.variant_attributes.first().pk
    )
    variant_value = "test-value"
    variables = {
        "productId": product_id,
        "sku": sku,
        "priceOverride": price_override,
        "attributes": [{"id": variant_id, "values": [variant_value]}],
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    assert response.status_code == 200

    content = get_graphql_content(response)
    data = content["data"]["productVariantCreate"]
    assert data["productErrors"] == []

    mock_update_product_minimal_variant_price_task.delay.assert_called_once_with(
        product.pk
    )


@patch(
    "saleor.graphql.product.mutations.products"
    ".update_product_minimal_variant_price_task"
)
def test_product_variant_update_updates_minimal_variant_price(
    mock_update_product_minimal_variant_price_task,
    staff_api_client,
    product,
    permission_manage_products,
):
    query = """
        mutation ProductVariantUpdate(
            $id: ID!,
            $priceOverride: Decimal,
        ) {
            productVariantUpdate(
                id: $id,
                input: {
                    priceOverride: $priceOverride,
                }
            ) {
                productVariant {
                    name
                }
                errors {
                    message
                    field
                }
            }
        }
    """
    variant = product.variants.first()
    variant_id = to_global_id("ProductVariant", variant.pk)
    price_override = "1.99"
    variables = {"id": variant_id, "priceOverride": price_override}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    assert response.status_code == 200

    content = get_graphql_content(response)
    data = content["data"]["productVariantUpdate"]
    assert data["errors"] == []

    mock_update_product_minimal_variant_price_task.delay.assert_called_once_with(
        product.pk
    )


@patch(
    "saleor.graphql.product.mutations.products"
    ".update_product_minimal_variant_price_task"
)
def test_product_variant_update_updates_invalid_variant_price(
    mock_update_product_minimal_variant_price_task,
    staff_api_client,
    product,
    permission_manage_products,
):
    query = """
        mutation ProductVariantUpdate(
            $id: ID!,
            $priceOverride: Decimal,
        ) {
            productVariantUpdate(
                id: $id,
                input: {
                    priceOverride: $priceOverride,
                }
            ) {
                productVariant {
                    name
                }
                productErrors {
                    field
                    message
                    code
                }
            }
        }
    """
    variant = product.variants.first()
    variant_id = to_global_id("ProductVariant", variant.pk)
    price_override = "-1.99"
    variables = {"id": variant_id, "priceOverride": price_override}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    assert response.status_code == 200

    content = get_graphql_content(response)
    data = content["data"]["productVariantUpdate"]
    assert data["productErrors"][0]["field"] == "priceOverride"
    assert data["productErrors"][0]["code"] == ProductErrorCode.INVALID.name


@patch(
    "saleor.graphql.product.mutations.products"
    ".update_product_minimal_variant_price_task"
)
def test_product_variant_update_updates_invalid_cost_price(
    mock_update_product_minimal_variant_price_task,
    staff_api_client,
    product,
    permission_manage_products,
):
    query = """
        mutation ProductVariantUpdate(
            $id: ID!,
            $costPrice: Decimal,
        ) {
            productVariantUpdate(
                id: $id,
                input: {
                    costPrice: $costPrice,
                }
            ) {
                productVariant {
                    name
                }
                productErrors {
                    field
                    message
                    code
                }
            }
        }
    """
    variant = product.variants.first()
    variant_id = to_global_id("ProductVariant", variant.pk)
    cost_price = "-1.99"
    variables = {"id": variant_id, "costPrice": cost_price}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    assert response.status_code == 200

    content = get_graphql_content(response)
    data = content["data"]["productVariantUpdate"]
    assert data["productErrors"][0]["field"] == "costPrice"
    assert data["productErrors"][0]["code"] == ProductErrorCode.INVALID.name


@patch(
    "saleor.graphql.product.mutations.products."
    "update_product_minimal_variant_price_task"
)
def test_product_variant_delete_updates_minimal_variant_price(
    mock_update_product_minimal_variant_price_task,
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

    mock_update_product_minimal_variant_price_task.delay.assert_called_once_with(
        product.pk
    )


@patch("saleor.product.utils.update_products_minimal_variant_prices_task")
def test_category_delete_updates_minimal_variant_price(
    mock_update_products_minimal_variant_prices_task,
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

    mock_update_products_minimal_variant_prices_task.delay.assert_called_once()
    (
        _call_args,
        call_kwargs,
    ) = mock_update_products_minimal_variant_prices_task.delay.call_args
    assert set(call_kwargs["product_ids"]) == set(p.pk for p in product_list)

    for product in product_list:
        product.refresh_from_db()
        assert not product.category


@patch(
    "saleor.graphql.product.mutations.products"
    ".update_products_minimal_variant_prices_of_catalogues_task"
)
def test_collection_add_products_updates_minimal_variant_price(
    mock_update_minimal_variant_prices_task,
    staff_api_client,
    sale,
    collection,
    product_list,
    permission_manage_products,
):
    sale.collections.add(collection)
    assert collection.products.count() == 0
    query = """
        mutation CollectionAddProducts($id: ID!, $products: [ID]!) {
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

    mock_update_minimal_variant_prices_task.delay.assert_called_once_with(
        product_ids=[p.pk for p in product_list]
    )


@patch(
    "saleor.graphql.product.mutations"
    ".products.update_products_minimal_variant_prices_of_catalogues_task"
)
def test_collection_remove_products_updates_minimal_variant_price(
    mock_update_minimal_variant_prices_task,
    staff_api_client,
    sale,
    collection,
    product_list,
    permission_manage_products,
):
    sale.collections.add(collection)
    assert collection.products.count() == 0
    query = """
        mutation CollectionRemoveProducts($id: ID!, $products: [ID]!) {
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

    mock_update_minimal_variant_prices_task.delay.assert_called_once_with(
        product_ids=[p.pk for p in product_list]
    )


@freeze_time("2010-05-31 12:00:01")
@patch(
    "saleor.graphql.discount.mutations"
    ".update_products_minimal_variant_prices_of_discount_task"
)
def test_sale_create_updates_products_minimal_variant_prices(
    mock_update_minimal_variant_prices_task,
    staff_api_client,
    permission_manage_discounts,
):
    query = """
    mutation SaleCreate(
            $name: String,
            $type: DiscountValueTypeEnum,
            $value: Decimal,
            $products: [ID]
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
    mock_update_minimal_variant_prices_task.delay.assert_called_once_with(sale_id)


@patch(
    "saleor.graphql.discount.mutations"
    ".update_products_minimal_variant_prices_of_discount_task"
)
def test_sale_update_updates_products_minimal_variant_prices(
    mock_update_minimal_variant_prices_task,
    staff_api_client,
    sale,
    permission_manage_discounts,
):
    query = """
    mutation SaleUpdate($id: ID!, $value: Decimal) {
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

    mock_update_minimal_variant_prices_task.delay.assert_called_once_with(sale.pk)


@patch(
    "saleor.graphql.discount.mutations"
    ".update_products_minimal_variant_prices_of_discount_task"
)
def test_sale_delete_updates_products_minimal_variant_prices(
    mock_update_minimal_variant_prices_task,
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

    mock_update_minimal_variant_prices_task.delay.assert_called_once_with(sale.pk)


@patch(
    "saleor.graphql.discount.mutations"
    ".update_products_minimal_variant_prices_of_catalogues_task"
)
def test_sale_add_catalogues_updates_products_minimal_variant_prices(
    mock_update_minimal_variant_prices_task,
    staff_api_client,
    sale,
    product,
    category,
    collection,
    permission_manage_discounts,
):
    query = """
        mutation SaleCataloguesAdd($id: ID!, $input: CatalogueInput!) {
            saleCataloguesAdd(id: $id, input: $input) {
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
    variables = {
        "id": sale_id,
        "input": {
            "products": [product_id],
            "collections": [collection_id],
            "categories": [category_id],
        },
    }

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_discounts]
    )
    assert response.status_code == 200

    content = get_graphql_content(response)
    assert content["data"]["saleCataloguesAdd"]["errors"] == []

    mock_update_minimal_variant_prices_task.delay.assert_called_once_with(
        product_ids=[product.pk],
        category_ids=[category.pk],
        collection_ids=[collection.pk],
    )


@patch(
    "saleor.graphql.discount.mutations"
    ".update_products_minimal_variant_prices_of_catalogues_task"
)
def test_sale_remove_catalogues_updates_products_minimal_variant_prices(
    mock_update_minimal_variant_prices_task,
    staff_api_client,
    sale,
    product,
    category,
    collection,
    permission_manage_discounts,
):
    assert product in sale.products.all()
    assert category in sale.categories.all()
    assert collection in sale.collections.all()
    query = """
        mutation SaleCataloguesRemove($id: ID!, $input: CatalogueInput!) {
            saleCataloguesRemove(id: $id, input: $input) {
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
    variables = {
        "id": sale_id,
        "input": {
            "products": [product_id],
            "collections": [collection_id],
            "categories": [category_id],
        },
    }

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_discounts]
    )
    assert response.status_code == 200

    content = get_graphql_content(response)
    assert content["data"]["saleCataloguesRemove"]["errors"] == []

    mock_update_minimal_variant_prices_task.delay.assert_called_once_with(  # noqa
        product_ids=[product.pk],
        category_ids=[category.pk],
        collection_ids=[collection.pk],
    )
