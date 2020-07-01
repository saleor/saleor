import graphene

from ..utils.product_variants import (
    get_products_from_global_ids,
    get_products_without_variants,
)


def test_get_products_without_variants(product_list):
    product_global_ids = [
        graphene.Node.to_global_id("Product", product.id) for product in product_list
    ]

    assert get_products_without_variants(product_global_ids) == []

    product = product_list[0]
    product.variants.first().delete()

    second_product = product_list[1]
    second_product.variants.first().delete()

    assert get_products_without_variants(product_global_ids) == [
        product.id,
        second_product.id,
    ]


def test_get_products_from_global_ids(product_list):
    product_global_ids = [
        graphene.Node.to_global_id("Product", product.id) for product in product_list
    ]
    product_ids = [str(product.id) for product in product_list]

    result = get_products_from_global_ids(product_global_ids)

    assert result == product_ids
