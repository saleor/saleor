from ..models import Product
from ..search import update_product_search_vector, update_products_search_vector


def test_update_product_search_vector(product_type, category):
    # given
    name = "Test product"
    description = "Test description"
    product = Product.objects.create(
        name=name,
        slug="test-product-111",
        product_type=product_type,
        category=category,
        description_plaintext=description,
    )
    assert not product.search_vector

    # when
    update_product_search_vector(product)

    # then
    assert product.search_vector


def test_update_products_search_vector(product_list):
    # given
    for product in product_list:
        product.search_vector = None
    Product.objects.bulk_update(product_list, ["search_vector"])

    # when
    update_products_search_vector(Product.objects.all())

    # then
    for product in product_list:
        product.refresh_from_db()
        assert product.search_vector
