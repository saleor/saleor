from collections import defaultdict
from copy import deepcopy
from enum import Enum
from typing import cast

import graphene
from django.db.models import Exists, OuterRef, QuerySet
from graphene.utils.str_converters import to_camel_case

from ...discount.models import Promotion, PromotionRule
from ...discount.utils import update_rule_variant_relation
from ...product.managers import ProductsQueryset, ProductVariantQueryset
from ...product.models import (
    Category,
    Collection,
    CollectionProduct,
    Product,
    ProductVariant,
)
from ..core.connection import where_filter_qs
from ..product.filters import (
    CategoryWhere,
    CollectionWhere,
    ProductVariantWhere,
    ProductWhere,
)

PREDICATE_OPERATOR_DATA_T = list[dict[str, list | dict | str | bool]]


class Operators(Enum):
    AND = "and"
    OR = "or"


# TODO: move to validators in promotion dir
def clean_predicate(predicate: dict[str, dict | list] | list):
    """Convert camel cases keys into snake case."""
    if isinstance(predicate, list):
        return [
            clean_predicate(item) if isinstance(item, dict | list) else item
            for item in predicate
        ]
    return {
        to_camel_case(key): clean_predicate(value)
        if isinstance(value, dict | list)
        else value
        for key, value in predicate.items()
    }


def get_products_for_promotion(
    promotion: Promotion, *, update_rule_variants=False
) -> ProductsQueryset:
    """Get products that are included in the promotion based on catalogue predicate."""
    variants = get_variants_for_promotion(
        promotion, update_rule_variants=update_rule_variants
    )
    return Product.objects.filter(Exists(variants.filter(product_id=OuterRef("id"))))


def get_products_for_rule(
    rule: PromotionRule, *, update_rule_variants=False
) -> ProductsQueryset:
    """Get products that are included in the rule based on catalogue predicate."""
    variants = get_variants_for_predicate(deepcopy(rule.catalogue_predicate))
    if update_rule_variants:
        rule.variants.set(variants)
    return Product.objects.filter(Exists(variants.filter(product_id=OuterRef("id"))))


def get_variants_for_promotion(
    promotion: Promotion, *, update_rule_variants=False
) -> ProductVariantQueryset:
    """Get variants that are included in the promotion based on catalogue predicate."""
    queryset = ProductVariant.objects.none()
    promotion_rule_variants = []
    PromotionRuleVariant = PromotionRule.variants.through
    rules = promotion.rules.all()
    for rule in rules:
        variants = get_variants_for_predicate(rule.catalogue_predicate)
        queryset |= variants
        if update_rule_variants:
            promotion_rule_variants.extend(
                [
                    PromotionRuleVariant(
                        promotionrule_id=rule.pk, productvariant_id=variant.pk
                    )
                    for variant in variants
                ]
            )
    if promotion_rule_variants:
        update_rule_variant_relation(rules, promotion_rule_variants)

    return queryset


def _handle_product_predicate(
    predicate_data: dict[str, dict | list],
) -> ProductVariantQueryset:
    product_qs = where_filter_qs(
        Product.objects.all(), {}, ProductWhere, predicate_data, None
    )
    return ProductVariant.objects.filter(
        Exists(product_qs.filter(id=OuterRef("product_id")))
    )


def _handle_variant_predicate(
    predicate_data: dict[str, dict | list],
) -> ProductVariantQueryset:
    return where_filter_qs(
        ProductVariant.objects.all(), {}, ProductVariantWhere, predicate_data, None
    )


def _handle_collection_predicate(
    predicate_data: dict[str, dict | list],
) -> ProductVariantQueryset:
    collection_qs = where_filter_qs(
        Collection.objects.all(), {}, CollectionWhere, predicate_data, None
    )
    collection_products = CollectionProduct.objects.filter(
        Exists(collection_qs.filter(id=OuterRef("collection_id")))
    )
    products = Product.objects.filter(
        Exists(collection_products.filter(product_id=OuterRef("id")))
    )
    return ProductVariant.objects.filter(
        Exists(products.filter(id=OuterRef("product_id")))
    )


def _handle_category_predicate(
    predicate_data: dict[str, dict | list],
) -> ProductVariantQueryset:
    category_qs = where_filter_qs(
        Category.objects.all(), {}, CategoryWhere, predicate_data, None
    )
    products = Product.objects.filter(
        Exists(category_qs.filter(id=OuterRef("category_id")))
    )
    return ProductVariant.objects.filter(
        Exists(products.filter(id=OuterRef("product_id")))
    )


PREDICATE_TO_HANDLE_METHOD = {
    "productPredicate": _handle_product_predicate,
    "variantPredicate": _handle_variant_predicate,
    "collectionPredicate": _handle_collection_predicate,
    "categoryPredicate": _handle_category_predicate,
}


def get_variants_for_predicate(
    predicate: dict, queryset: ProductVariantQueryset | None = None
) -> ProductVariantQueryset:
    """Get variants that met the predicate conditions."""
    if not predicate:
        return ProductVariant.objects.none()

    if queryset is None:
        queryset = ProductVariant.objects.all()
    and_data: list[dict] | None = predicate.pop("AND", None)
    or_data: list[dict] | None = predicate.pop("OR", None)

    if and_data:
        queryset = _handle_and_data(queryset, and_data)

    if or_data:
        queryset = _handle_or_data(queryset, or_data)

    if predicate:
        queryset = _handle_catalogue_predicate(queryset, predicate, Operators.AND)

    return queryset


def _handle_and_data(
    queryset: ProductVariantQueryset, data: PREDICATE_OPERATOR_DATA_T
) -> ProductVariantQueryset:
    for predicate_data in data:
        if contains_filter_operator(predicate_data):
            queryset &= get_variants_for_predicate(predicate_data, queryset)
        else:
            queryset = _handle_catalogue_predicate(
                queryset, predicate_data, Operators.AND
            )
    return queryset


def _handle_or_data(
    queryset: ProductVariantQueryset, data: PREDICATE_OPERATOR_DATA_T
) -> ProductVariantQueryset:
    qs = queryset.model.objects.none()
    for predicate_data in data:
        if contains_filter_operator(predicate_data):
            qs |= get_variants_for_predicate(predicate_data, queryset)
        else:
            qs = _handle_catalogue_predicate(qs, predicate_data, Operators.OR)
    queryset &= qs
    return queryset


def contains_filter_operator(input: dict[str, dict | str | list | bool]) -> bool:
    return any([operator in input for operator in ["AND", "OR", "NOT"]])


def _handle_catalogue_predicate(
    queryset: ProductVariantQueryset,
    predicate_data: dict[str, dict | str | list | bool],
    operator,
) -> ProductVariantQueryset:
    for field, handle_method in PREDICATE_TO_HANDLE_METHOD.items():
        if field_data := predicate_data.get(field):
            field_data = cast(dict[str, dict | list], field_data)
            if operator == Operators.AND:
                queryset &= handle_method(field_data)
            else:
                queryset |= handle_method(field_data)
    return queryset


def convert_migrated_sale_predicate_to_model_ids(
    catalogue_predicate,
) -> dict[str, list[int]] | None:
    """Convert global ids from catalogue predicate of Promotion created from old sale.

    All migrated sales have related PromotionRule with "OR" catalogue predicate. This
    function converts:
        {
            "OR": [
                {"collectionPredicate": {"ids": ["UHJvZHV3","UHJvZHV2","UHJvZHV1]}},
                {"productPredicate": {"ids": ["UHJvZHV9","UHJvZHV8","UHJvZHV7]}},
            ]
        }
    into:
        {
            "collectionPredicate": [1,2,3],
            "productPredicate": [9,8,7],
        }
    """
    if catalogue_predicate.get("OR"):
        predicates = {
            list(item.keys())[0]: list(item.values())[0]["ids"]
            for item in catalogue_predicate["OR"]
        }
        for key, ids in predicates.items():
            predicates[key] = [graphene.Node.from_global_id(id)[1] for id in ids]
        return predicates
    return None


CatalogueInfo = defaultdict[str, set[int | str]]
PREDICATE_TO_CATALOGUE_INFO_MAP = {
    "collectionPredicate": "collections",
    "categoryPredicate": "categories",
    "productPredicate": "products",
    "variantPredicate": "variants",
}


def convert_migrated_sale_predicate_to_catalogue_info(
    catalogue_predicate,
) -> CatalogueInfo:
    """Convert predicate of Promotion created from old sale into CatalogueInfo object.

    All migrated sales have related PromotionRule with "OR" catalogue predicate. This
    function converts:
        {
            "OR": [
                {"collectionPredicate": {"ids": ["UHJvZHV3","UHJvZHV2","UHJvZHV1"]}},
                {"productPredicate": {"ids": ["UHJvZHV9","UHJvZHV8","UHJvZHV7"]}},
            ]
        }
    into:
        {
            "collections": {"UHJvZHV3","UHJvZHV2","UHJvZHV1"},
            "categories": {},
            "products": {"UHJvZHV9","UHJvZHV8","UHJvZHV7"},
            "variants": {},
        }
    """
    catalogue_info: CatalogueInfo = defaultdict(set)
    for field in PREDICATE_TO_CATALOGUE_INFO_MAP.values():
        catalogue_info[field] = set()

    if catalogue_predicate.get("OR"):
        predicates = {
            list(item.keys())[0]: list(item.values())[0]["ids"]
            for item in catalogue_predicate["OR"]
        }
        for predicate_name, field in PREDICATE_TO_CATALOGUE_INFO_MAP.items():
            catalogue_info[field] = set(predicates.get(predicate_name, {}))

    return catalogue_info


def convert_catalogue_info_into_predicate(catalogue_info: CatalogueInfo) -> dict:
    catalogue = []
    collection_ids = catalogue_info.get("collections")
    category_ids = catalogue_info.get("categories")
    product_ids = catalogue_info.get("products")
    variants_ids = catalogue_info.get("variants")
    if collection_ids:
        catalogue.append({"collectionPredicate": {"ids": list(collection_ids)}})
    if category_ids:
        catalogue.append({"categoryPredicate": {"ids": list(category_ids)}})
    if product_ids:
        catalogue.append({"productPredicate": {"ids": list(product_ids)}})
    if variants_ids:
        catalogue.append({"variantPredicate": {"ids": list(variants_ids)}})
    if catalogue:
        return {"OR": catalogue}
    return {}


def get_categories_from_predicate(catalogue_predicate) -> QuerySet:
    return where_filter_qs(
        Category.objects.all(), {}, CategoryWhere, catalogue_predicate, None
    ).all()


def merge_catalogues_info(
    catalogue_1: CatalogueInfo, catalogue_2: CatalogueInfo
) -> CatalogueInfo:
    new_catalogue = deepcopy(catalogue_1)
    new_catalogue["collections"].update(catalogue_2.get("collections", set()))
    new_catalogue["categories"].update(catalogue_2.get("categories", set()))
    new_catalogue["products"].update(catalogue_2.get("products", set()))
    new_catalogue["variants"].update(catalogue_2.get("variants", set()))
    return new_catalogue


def subtract_catalogues_info(
    catalogue_1: CatalogueInfo, catalogue_2: CatalogueInfo
) -> CatalogueInfo:
    new_catalogue = deepcopy(catalogue_1)
    new_catalogue["collections"] -= catalogue_2.get("collections", set())
    new_catalogue["categories"] -= catalogue_2.get("categories", set())
    new_catalogue["products"] -= catalogue_2.get("products", set())
    new_catalogue["variants"] -= catalogue_2.get("variants", set())
    return new_catalogue


def create_catalogue_predicate(collection_ids, category_ids, product_ids, variant_ids):
    predicate: dict[str, list] = {"OR": []}
    if collection_ids:
        predicate["OR"].append({"collectionPredicate": {"ids": collection_ids}})
    if category_ids:
        predicate["OR"].append({"categoryPredicate": {"ids": category_ids}})
    if product_ids:
        predicate["OR"].append({"productPredicate": {"ids": product_ids}})
    if variant_ids:
        predicate["OR"].append({"variantPredicate": {"ids": variant_ids}})
    if not predicate.get("OR"):
        predicate = {}

    return predicate
