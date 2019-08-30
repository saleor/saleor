from decimal import Decimal
from unittest.mock import patch

from django.core.management import call_command
from django.urls import reverse
from prices import Money

from saleor.discount import DiscountValueType
from saleor.product.models import Product, ProductVariant
from saleor.product.tasks import (
    update_all_products_minimal_variant_prices_task,
    update_products_minimal_variant_prices_of_catalogues,
)
from saleor.product.utils.variant_prices import update_product_minimal_variant_price


def test_update_product_minimal_variant_price(product):
    variant = product.variants.first()
    variant.price_override = Money("4.99", "USD")
    variant.save()

    assert product.minimal_variant_price == product.price == Money("10", "USD")
    update_product_minimal_variant_price(product)
    assert product.minimal_variant_price == variant.price_override


def test_update_products_minimal_variant_prices_of_catalogues_for_product(product):
    variant = ProductVariant(
        product=product,
        sku="SKU_MINIMAL_VARIANT_PRICE",
        price_override=Money("0.99", "USD"),
    )
    variant.save()
    product.refresh_from_db()
    assert product.minimal_variant_price == product.price == Money("10", "USD")
    update_products_minimal_variant_prices_of_catalogues(product_ids=[product.pk])
    product.refresh_from_db()
    assert product.minimal_variant_price == variant.price_override


def test_update_products_minimal_variant_prices_of_catalogues_for_category(
    category, product
):
    variant = ProductVariant(
        product=product,
        sku="SKU_MINIMAL_VARIANT_PRICE",
        price_override=Money("0.89", "USD"),
    )
    variant.save()
    product.refresh_from_db()
    assert product.minimal_variant_price == product.price == Money("10", "USD")
    update_products_minimal_variant_prices_of_catalogues(
        category_ids=[product.category_id]
    )
    product.refresh_from_db()
    assert product.minimal_variant_price == variant.price_override


def test_update_products_minimal_variant_prices_of_catalogues_for_collection(
    collection, product
):
    variant = ProductVariant(
        product=product,
        sku="SKU_MINIMAL_VARIANT_PRICE",
        price_override=Money("0.79", "USD"),
    )
    variant.save()
    product.refresh_from_db()
    collection.products.add(product)
    assert product.minimal_variant_price == product.price == Money("10", "USD")
    update_products_minimal_variant_prices_of_catalogues(collection_ids=[collection.pk])
    product.refresh_from_db()
    assert product.minimal_variant_price == variant.price_override


def test_update_all_products_minimal_variant_prices_task(product_list):
    price_override = Money("0.01", "USD")
    for product in product_list:
        assert product.minimal_variant_price > price_override
        variant = product.variants.first()
        variant.price_override = price_override
        variant.save()
        # Check that "variant.save()" doesn't update the "minimal_variant_price"
        assert product.minimal_variant_price > price_override

    update_all_products_minimal_variant_prices_task.apply()
    for product in product_list:
        product.refresh_from_db()
        assert product.minimal_variant_price == price_override


def test_product_objects_create_sets_default_minimal_variant_price(
    product_type, category
):
    product1 = Product.objects.create(
        name="Test product 1",
        price=Money("10.00", "USD"),
        category=category,
        product_type=product_type,
        is_published=True,
    )
    assert product1.minimal_variant_price
    assert product1.price == product1.minimal_variant_price == Money("10", "USD")

    product2 = Product.objects.create(
        name="Test product 2",
        price=Money("10.00", "USD"),
        minimal_variant_price=Money("20.00", "USD"),
        category=category,
        product_type=product_type,
        is_published=True,
    )
    assert product2.minimal_variant_price
    assert product2.price != product2.minimal_variant_price
    assert product2.minimal_variant_price == Money("20", "USD")


def test_product_objects_bulk_create_sets_default_minimal_variant_price(
    product_type, category
):
    [product1, product2] = Product.objects.bulk_create(
        [
            Product(
                name="Test product 1",
                price=Money("10.00", "USD"),
                category=category,
                product_type=product_type,
                is_published=True,
            ),
            Product(
                name="Test product 2",
                price=Money("10.00", "USD"),
                minimal_variant_price=Money("20.00", "USD"),
                category=category,
                product_type=product_type,
                is_published=True,
            ),
        ]
    )

    assert product1.minimal_variant_price
    assert product1.price == product1.minimal_variant_price == Money("10", "USD")

    assert product2.minimal_variant_price
    assert product2.price != product2.minimal_variant_price
    assert product2.minimal_variant_price == Money("20", "USD")


def test_product_variant_objects_create_updates_minimal_variant_price(product):
    assert product.minimal_variant_price == Money("10.00", "USD")
    ProductVariant.objects.create(
        product=product, sku="1", price_override=Money("1.00", "USD"), quantity=1
    )
    product.refresh_from_db()
    assert product.minimal_variant_price == Money("1.00", "USD")


def test_product_variant_objects_bulk_create_updates_minimal_variant_price(product):
    assert product.minimal_variant_price == Money("10.00", "USD")
    ProductVariant.objects.bulk_create(
        [
            ProductVariant(
                product=product,
                sku="1",
                price_override=Money("1.00", "USD"),
                quantity=1,
            ),
            ProductVariant(
                product=product,
                sku="2",
                price_override=Money("5.00", "USD"),
                quantity=1,
            ),
        ]
    )
    product.refresh_from_db()
    assert product.minimal_variant_price == Money("1.00", "USD")


def test_dashboard_product_create_view_sets_minimal_variant_price(
    admin_client, product_type, category
):
    url = reverse("dashboard:product-add", kwargs={"type_pk": product_type.pk})
    data = {
        "name": "Product name",
        "description": "Description.",
        "price_0": "9.99",
        "price_1": "USD",
        "category": category.pk,
    }

    response = admin_client.post(url, data)
    assert response.status_code == 302
    assert Product.objects.count() == 1
    product = Product.objects.get()
    assert product.minimal_variant_price == product.price == Money("9.99", "USD")


def test_dashboard_product_variant_create_view_updates_minimal_variant_price(
    admin_client, product
):
    url = reverse("dashboard:variant-add", kwargs={"product_pk": product.pk})
    data = {
        "sku": "ACME/1/2/3",
        "price_override_0": "4.99",
        "price_override_1": product.currency,
        "quantity": 1,
    }

    response = admin_client.post(url, data)
    assert response.status_code == 302

    product.refresh_from_db()

    assert product.variants.count() == 2
    assert product.minimal_variant_price != product.price
    assert product.minimal_variant_price == Money("4.99", "USD")


def test_dashboard_product_variant_delete_view_updates_minimal_variant_price(
    admin_client, product
):
    # Set "price_override" on the variant to lower the "minimal_variant_price"
    assert product.minimal_variant_price == product.price == Money("10", "USD")
    variant = product.variants.get()
    variant.price_override = Money("4.99", "USD")
    variant.save()
    update_product_minimal_variant_price(product)
    product.refresh_from_db()
    assert product.minimal_variant_price == variant.price_override

    url = reverse(
        "dashboard:variant-delete",
        kwargs={"product_pk": product.pk, "variant_pk": variant.pk},
    )

    response = admin_client.post(url)
    assert response.status_code == 302

    product.refresh_from_db()
    assert product.minimal_variant_price == product.price


def test_dashboard_sale_of_product_create_view_updates_minimal_variant_price(
    admin_client, product
):
    # Store the old "minimal_variant_price"
    old_minimal_variant_price = product.minimal_variant_price
    # Create the "Sale" object of the given product
    url = reverse("dashboard:sale-add")
    data = {
        "name": "Half price products",
        "type": DiscountValueType.PERCENTAGE,
        "value": "50",
        "start_date": "2019-07-11 00:00:01",
        "products": [product.pk],
    }
    response = admin_client.post(url, data)
    assert response.status_code == 302

    product.refresh_from_db()
    assert product.minimal_variant_price == Decimal("0.5") * old_minimal_variant_price


def test_dashboard_sale_of_category_create_view_updates_minimal_variant_price(
    admin_client, product
):
    category = product.category
    # Store the old "minimal_variant_price"
    old_minimal_variant_price = product.minimal_variant_price
    # Create the "Sale" object of the given category
    url = reverse("dashboard:sale-add")
    data = {
        "name": "Half price category",
        "type": DiscountValueType.PERCENTAGE,
        "value": "50",
        "start_date": "2019-07-11 00:00:01",
        "categories": [category.pk],
    }
    response = admin_client.post(url, data)
    assert response.status_code == 302

    product.refresh_from_db()
    assert product.minimal_variant_price == Decimal("0.5") * old_minimal_variant_price


def test_dashboard_sale_of_collection_create_view_updates_minimal_variant_price(
    admin_client, product, collection
):
    collection.products.add(product)
    # Store the old "minimal_variant_price"
    old_minimal_variant_price = product.minimal_variant_price
    # Create the "Sale" object of the given collection
    url = reverse("dashboard:sale-add")
    data = {
        "name": "Half price collection",
        "type": DiscountValueType.PERCENTAGE,
        "value": "50",
        "start_date": "2019-07-11 00:00:01",
        "collections": [collection.pk],
    }
    response = admin_client.post(url, data)
    assert response.status_code == 302

    product.refresh_from_db()
    assert product.minimal_variant_price == Decimal("0.5") * old_minimal_variant_price


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
