from ..models import Product
from ..search import update_products_search_vector


def test_update_products_search_vector(product_list):
    # given
    for product in product_list:
        product.search_vector = None
    Product.objects.bulk_update(product_list, ["search_vector"])

    # when
    update_products_search_vector(Product.objects.all().values_list("id", flat=True))

    # then
    for product in product_list:
        product.refresh_from_db()
        assert product.search_vector
