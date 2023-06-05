import graphene

from ..utils import get_variants_for_predicate


def test_get_variants_for_predicate_with_or(product_with_two_variants, variant):
    # given
    catalogue_predicate = {
        "OR": [
            {
                "variantPredicate": {
                    "ids": [graphene.Node.to_global_id("ProductVariant", variant.id)]
                }
            },
            {
                "productPredicate": {
                    "ids": [
                        graphene.Node.to_global_id(
                            "Product", product_with_two_variants.id
                        )
                    ]
                }
            },
        ]
    }

    # when
    variants = get_variants_for_predicate(catalogue_predicate)

    # then
    assert variant in variants
    for variant in product_with_two_variants.variants.all():
        assert variant in variants


def test_get_variants_for_predicate_with_and(collection, product_list):
    # given
    product_in_collection = product_list[1]
    collection.products.add(product_in_collection)
    catalogue_predicate = {
        "AND": [
            {
                "collectionPredicate": {
                    "ids": [graphene.Node.to_global_id("Collection", collection.id)]
                }
            },
            {
                "productPredicate": {
                    "ids": [
                        graphene.Node.to_global_id("Product", product.id)
                        for product in product_list
                    ]
                }
            },
        ]
    }

    # when
    variants = get_variants_for_predicate(catalogue_predicate)

    # then
    assert len(variants) == product_in_collection.variants.count()
    for variant in product_in_collection.variants.all():
        assert variant in variants


def test_get_variants_for_product_predicate(product_with_two_variants, variant):
    # given
    catalogue_predicate = {
        "productPredicate": {
            "ids": [graphene.Node.to_global_id("Product", product_with_two_variants.id)]
        }
    }

    # when
    variants = get_variants_for_predicate(catalogue_predicate)

    # then
    assert len(variants) == product_with_two_variants.variants.count()
    assert variant not in variants
    for variant in product_with_two_variants.variants.all():
        assert variant in variants


def test_get_variants_for_variant_predicate(product_with_two_variants, variant):
    # given
    catalogue_predicate = {
        "variantPredicate": {
            "ids": [
                graphene.Node.to_global_id("ProductVariant", v.id)
                for v in product_with_two_variants.variants.all()
            ]
        }
    }

    # when
    variants = get_variants_for_predicate(catalogue_predicate)

    # then
    assert len(variants) == product_with_two_variants.variants.count()
    assert variant not in variants
    for variant in product_with_two_variants.variants.all():
        assert variant in variants


def test_get_variants_for_category_predicate(
    categories, product, product_with_two_variants
):
    # given
    category = categories[0]
    catalogue_predicate = {
        "categoryPredicate": {
            "ids": [graphene.Node.to_global_id("Category", categories[0].id)]
        }
    }
    product.category = category
    product.save(update_fields=["category"])

    # when
    variants = get_variants_for_predicate(catalogue_predicate)

    # then
    assert len(variants) == product.variants.count()
    for variant in product.variants.all():
        assert variant in variants
    for variant in product_with_two_variants.variants.all():
        assert variant not in variants


def test_get_variants_for_collection_predicate(
    collection, product, product_with_two_variants
):
    # given
    catalogue_predicate = {
        "collectionPredicate": {
            "ids": [graphene.Node.to_global_id("Collection", collection.id)]
        }
    }
    collection.products.add(product)

    # when
    variants = get_variants_for_predicate(catalogue_predicate)

    # then
    assert len(variants) == product.variants.count()
    for variant in product.variants.all():
        assert variant in variants
    for variant in product_with_two_variants.variants.all():
        assert variant not in variants


def test_get_variants_for_predicate_with_nested_conditions(
    product_list, collection, variant
):
    # given
    product_in_collection = product_list[1]
    collection.products.add(product_in_collection)
    catalogue_predicate = {
        "OR": [
            {
                "variantPredicate": {
                    "ids": [graphene.Node.to_global_id("ProductVariant", variant.id)]
                }
            },
            {
                "AND": [
                    {
                        "collectionPredicate": {
                            "ids": [
                                graphene.Node.to_global_id("Collection", collection.id)
                            ]
                        }
                    },
                    {
                        "productPredicate": {
                            "ids": [
                                graphene.Node.to_global_id("Product", product.id)
                                for product in product_list
                            ]
                        }
                    },
                ]
            },
        ]
    }

    # when
    variants = get_variants_for_predicate(catalogue_predicate)

    # then
    assert len(variants) == product_in_collection.variants.count() + 1
    assert variant in variants
    for product_variant in product_in_collection.variants.all():
        assert product_variant in variants
