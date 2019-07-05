from django.urls import reverse
from prices import Money

from saleor.product.models import Product, ProductVariant
from saleor.product.utils.variant_prices import update_product_minimal_variant_price


def test_update_product_minimal_variant_price(product):
    assert product.minimal_variant_price == product.price == Money("10", "USD")
    variant = product.variants.first()
    variant.price_override = Money("4.99", "USD")
    variant.save()

    update_product_minimal_variant_price(product)
    assert product.minimal_variant_price == variant.price_override


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
        "price": "9.99",
        "category": category.pk,
    }

    response = admin_client.post(url, data)
    assert response.status_code == 302
    [product] = Product.objects.all()  # Also checks there is only one product
    assert product.minimal_variant_price == product.price == Money("9.99", "USD")


def test_dashboard_product_variant_create_view_updates_minimal_variant_price(
    admin_client, product
):
    url = reverse("dashboard:variant-add", kwargs={"product_pk": product.pk})
    data = {"sku": "ACME/1/2/3", "price_override": "4.99", "quantity": 1}

    response = admin_client.post(url, data)
    assert response.status_code == 302

    product.refresh_from_db()

    [old_variant, new_variant] = product.variants.all()
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
