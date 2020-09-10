from unittest.mock import patch

from django.core.management import call_command
from graphql_relay import to_global_id
from prices import Money

from ...graphql.tests.utils import get_graphql_content
from ..models import ProductVariant
from ..tasks import (
    update_products_minimal_variant_prices_of_catalogues,
    update_products_minimal_variant_prices_task,
)
from ..utils.variant_prices import update_product_minimal_variant_price


def test_update_product_minimal_variant_price(product):
    variant = product.variants.first()
    variant.price = Money("4.99", "USD")
    variant.save()
    product.refresh_from_db()

    assert product.minimal_variant_price == Money("10", "USD")
    update_product_minimal_variant_price(product)
    assert product.minimal_variant_price == variant.price


def test_update_products_minimal_variant_prices_of_catalogues_for_product(product):
    variant = ProductVariant(
        product=product, sku="SKU_MINIMAL_VARIANT_PRICE", price=Money("0.99", "USD"),
    )
    variant.save()
    product.refresh_from_db()
    assert product.minimal_variant_price == Money("10", "USD")
    update_products_minimal_variant_prices_of_catalogues(product_ids=[product.pk])
    product.refresh_from_db()
    assert product.minimal_variant_price == variant.price


def test_update_products_minimal_variant_prices_of_catalogues_for_category(
    category, product
):
    variant = ProductVariant(
        product=product, sku="SKU_MINIMAL_VARIANT_PRICE", price=Money("0.89", "USD"),
    )
    variant.save()
    product.refresh_from_db()
    assert product.minimal_variant_price == Money("10", "USD")
    update_products_minimal_variant_prices_of_catalogues(
        category_ids=[product.category_id]
    )
    product.refresh_from_db()
    assert product.minimal_variant_price == variant.price


def test_update_products_minimal_variant_prices_of_catalogues_for_collection(
    collection, product
):
    variant = ProductVariant(
        product=product, sku="SKU_MINIMAL_VARIANT_PRICE", price=Money("0.79", "USD"),
    )
    variant.save()
    product.refresh_from_db()
    collection.products.add(product)
    assert product.minimal_variant_price == Money("10", "USD")
    update_products_minimal_variant_prices_of_catalogues(collection_ids=[collection.pk])
    product.refresh_from_db()
    assert product.minimal_variant_price == variant.price


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
            $basePrice: PositiveDecimal!,
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


def test_update_products_minimal_variant_prices_task(product_list):
    price = Money("0.01", "USD")
    for product in product_list:
        assert product.minimal_variant_price is None
        variant = product.variants.first()
        variant.price = price
        variant.save()
        # Check that "variant.save()" doesn't update the "minimal_variant_price"
        assert product.minimal_variant_price is None

    update_products_minimal_variant_prices_task.apply(
        kwargs={"product_ids": [product.pk for product in product_list]}
    )
    for product in product_list:
        product.refresh_from_db()
        assert product.minimal_variant_price == price


def test_product_variant_objects_create_updates_minimal_variant_price(product):
    assert product.minimal_variant_price == Money("10.00", "USD")
    ProductVariant.objects.create(product=product, sku="1", price=Money("1.00", "USD"))
    product.refresh_from_db()
    assert product.minimal_variant_price == Money("1.00", "USD")


def test_product_variant_objects_bulk_create_updates_minimal_variant_price(product):
    assert product.minimal_variant_price == Money("10.00", "USD")
    ProductVariant.objects.bulk_create(
        [
            ProductVariant(product=product, sku="1", price=Money("1.00", "USD")),
            ProductVariant(product=product, sku="2", price=Money("5.00", "USD")),
        ]
    )
    product.refresh_from_db()
    assert product.minimal_variant_price == Money("1.00", "USD")


@patch(
    "saleor.product.management.commands"
    ".update_all_products_minimal_variant_prices"
    ".update_product_minimal_variant_price"
)
def test_management_commmand_update_all_products_minimal_variant_price(
    mock_update_product_minimal_variant_price, product_list
):
    call_command("update_all_products_minimal_variant_prices")
    call_args_list = mock_update_product_minimal_variant_price.call_args_list
    for (args, kwargs), product in zip(call_args_list, product_list):
        assert args[0] == product
