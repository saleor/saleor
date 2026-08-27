from ....context import SaleorContext
from ...dataloaders.products import (
    CollectionsByVariantIdLoader,
    ImagesByProductVariantIdLoader,
    MediaByProductVariantIdLoader,
    ProductByVariantIdLoader,
    ProductMediaByIdLoader,
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


def test_product_by_variant_id_loader_with_missing_variant(variant):
    # given
    context = SaleorContext()

    # when
    products = (
        ProductByVariantIdLoader(context).batch_load([variant.pk, MISSING_PK]).get()
    )

    # then
    assert products == [variant.product, None]


def test_media_by_product_variant_id_loader_with_missing_media(
    variant_with_image, monkeypatch
):
    """Media the loader cannot find (e.g. replica lag) is skipped, not a crash."""
    # given
    context = SaleorContext()
    monkeypatch.setattr(
        ProductMediaByIdLoader, "batch_load", lambda self, keys: [None] * len(keys)
    )

    # when
    media = (
        MediaByProductVariantIdLoader(context).batch_load([variant_with_image.pk]).get()
    )

    # then
    assert media == [[]]


def test_images_by_product_variant_id_loader_with_missing_media(
    variant_with_image, monkeypatch
):
    """Media the loader cannot find (e.g. replica lag) is skipped, not a crash."""
    # given
    context = SaleorContext()
    monkeypatch.setattr(
        ProductMediaByIdLoader, "batch_load", lambda self, keys: [None] * len(keys)
    )

    # when
    media = (
        ImagesByProductVariantIdLoader(context)
        .batch_load([variant_with_image.pk])
        .get()
    )

    # then
    assert media == [[]]
