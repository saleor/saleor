from ....context import SaleorContext
from ...dataloaders.products import (
    CollectionsByVariantIdLoader,
    ProductTypeByProductIdLoader,
    ProductTypeByVariantIdLoader,
)

MISSING_PK = -1
"""A pk that can never match a row, standing in for a replica that lags behind."""


def test_product_type_by_product_id_loader_with_missing_product(product):
    # given
    context = SaleorContext()

    # when
    product_types = (
        ProductTypeByProductIdLoader(context).batch_load([product.pk, MISSING_PK]).get()
    )

    # then
    assert product_types == [product.product_type, None]


def test_product_type_by_variant_id_loader_with_missing_variant(variant):
    # given
    context = SaleorContext()

    # when
    product_types = (
        ProductTypeByVariantIdLoader(context).batch_load([variant.pk, MISSING_PK]).get()
    )

    # then
    assert product_types == [variant.product.product_type, None]


def test_collections_by_variant_id_loader_with_missing_variant(
    variant, published_collection
):
    # given
    published_collection.products.add(variant.product)
    context = SaleorContext()

    # when
    collections = (
        CollectionsByVariantIdLoader(context).batch_load([variant.pk, MISSING_PK]).get()
    )

    # then
    assert collections == [[published_collection], []]
