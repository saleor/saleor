from ..utils import get_products_ids_without_variants


def test_get_products_ids_without_variants(product_list):
    assert get_products_ids_without_variants(product_list) == []

    product = product_list[0]
    product.variants.all().delete()

    second_product = product_list[1]
    second_product.variants.all().delete()

    assert get_products_ids_without_variants(product_list) == [
        product.id,
        second_product.id,
    ]
