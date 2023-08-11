from decimal import Decimal

import graphene

from ....discount import RewardValueType
from ....discount.models import Promotion, PromotionRule
from ..utils import (
    convert_migrated_sale_predicate_to_catalogue_info,
    get_variants_for_predicate,
    get_variants_for_promotion,
    merge_migrated_sale_predicates,
)


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


def test_get_variants_for_variant_predicate_empty_predicate_data(
    product_with_two_variants,
):
    # given
    catalogue_predicate = {}

    # when
    variants = get_variants_for_predicate(catalogue_predicate)

    # then
    assert len(variants) == 0


def test_get_variants_for_promotion(
    variant, product_with_two_variants, product_variant_list
):
    # given
    reward_value = Decimal("2")
    promotion = Promotion.objects.create(
        name="Promotion",
    )
    PromotionRule.objects.bulk_create(
        [
            PromotionRule(
                name="Percentage promotion rule 1",
                promotion=promotion,
                catalogue_predicate={
                    "variantPredicate": {
                        "ids": [
                            graphene.Node.to_global_id("ProductVariant", variant.id)
                        ]
                    }
                },
                reward_value_type=RewardValueType.FIXED,
                reward_value=reward_value,
            ),
            PromotionRule(
                name="Percentage promotion rule 2",
                promotion=promotion,
                catalogue_predicate={
                    "productPredicate": {
                        "ids": [
                            graphene.Node.to_global_id(
                                "Product", product_with_two_variants.id
                            )
                        ]
                    }
                },
                reward_value_type=RewardValueType.FIXED,
                reward_value=reward_value,
            ),
        ]
    )

    # when
    variants = get_variants_for_promotion(promotion)

    # then
    assert len(variants) == product_with_two_variants.variants.count() + 1
    assert variant in variants
    for variant in product_with_two_variants.variants.all():
        assert variant in variants


def test_convert_migrated_sale_predicate_to_catalogue_info(
    promotion_converted_from_sale, product, category, collection, variant
):
    # given
    rule = promotion_converted_from_sale.rules.first()
    predicate = rule.catalogue_predicate
    assert len(predicate["OR"]) == 4
    expected_result = {
        "categories": {graphene.Node.to_global_id("Category", category.id)},
        "collections": {graphene.Node.to_global_id("Collection", collection.id)},
        "products": {graphene.Node.to_global_id("Product", product.id)},
        "variants": {graphene.Node.to_global_id("ProductVariant", variant.id)},
    }

    # when
    catalogue_info = convert_migrated_sale_predicate_to_catalogue_info(predicate)

    # then
    assert catalogue_info == expected_result


def test_merge_migrated_sale_predicate(
    collection_list, category_list, product_list, product_variant_list
):
    # given
    collection_ids = [
        graphene.Node.to_global_id("Collection", item.id) for item in collection_list
    ]
    category_ids = [
        graphene.Node.to_global_id("Category", item.id) for item in category_list
    ]
    product_ids = [
        graphene.Node.to_global_id("Product", item.id) for item in product_list
    ]
    variant_ids = [
        graphene.Node.to_global_id("ProductVariant", item.id)
        for item in product_variant_list
    ]

    predicate_1 = {
        "OR": [
            {"collectionPredicate": {"ids": [collection_ids[0]]}},
            {"categoryPredicate": {"ids": [category_ids[0]]}},
            {"productPredicate": {"ids": [product_ids[0]]}},
            {"variantPredicate": {"ids": [variant_ids[0]]}},
        ]
    }

    predicate_2 = {
        "OR": [
            {"collectionPredicate": {"ids": [collection_ids[1]]}},
            {"categoryPredicate": {"ids": category_ids[:2]}},
            {"productPredicate": {"ids": [product_ids[0]]}},
            {"variantPredicate": {"ids": [variant_ids[2]]}},
        ]
    }

    expected_predicate = {
        "OR": [
            {"collectionPredicate": {"ids": collection_ids[:2]}},
            {"categoryPredicate": {"ids": category_ids[:2]}},
            {"productPredicate": {"ids": [product_ids[0]]}},
            {"variantPredicate": {"ids": [variant_ids[0], variant_ids[2]]}},
        ]
    }

    # when
    merged_predicate = merge_migrated_sale_predicates(predicate_1, predicate_2)

    # then
    assert merged_predicate == expected_predicate
