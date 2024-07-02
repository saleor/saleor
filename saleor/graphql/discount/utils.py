from collections import defaultdict
from copy import deepcopy
from enum import Enum
from typing import Any, Optional, Union, cast

import graphene
from django.conf import settings
from django.db.models import Exists, OuterRef, QuerySet
from graphene.utils.str_converters import to_snake_case

from ...checkout.models import Checkout
from ...discount.models import Promotion, PromotionRule
from ...discount.utils.promotion import update_rule_variant_relation
from ...order.models import Order
from ...product.managers import ProductsQueryset, ProductVariantQueryset
from ...product.models import (
    Category,
    Collection,
    CollectionProduct,
    Product,
    ProductVariant,
)
from ..checkout.filters import CheckoutDiscountedObjectWhere
from ..core.connection import where_filter_qs
from ..order.filters import OrderDiscountedObjectWhere
from ..product.filters import (
    CategoryWhere,
    CollectionWhere,
    ProductVariantWhere,
    ProductWhere,
)

PREDICATE_OPERATOR_DATA_T = list[dict[str, Union[list, dict, str, bool]]]


class PredicateObjectType(Enum):
    CATALOGUE = "catalogue"
    CHECKOUT = "checkout"
    ORDER = "order"


class Operators(Enum):
    AND = "and"
    OR = "or"


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
    variants = get_variants_for_catalogue_predicate(deepcopy(rule.catalogue_predicate))
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
        variants = get_variants_for_catalogue_predicate(rule.catalogue_predicate)
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
    predicate_data: dict[str, Union[dict, list]], variant_qs: QuerySet[ProductVariant]
) -> ProductVariantQueryset:
    product_qs = where_filter_qs(
        Product.objects.filter(Exists(variant_qs.filter(product_id=OuterRef("id")))),
        {},
        ProductWhere,
        predicate_data,
        None,
    )
    return ProductVariant.objects.filter(
        Exists(product_qs.filter(id=OuterRef("product_id")))
    )


def _handle_variant_predicate(
    predicate_data: dict[str, Union[dict, list]], variant_qs: QuerySet[ProductVariant]
) -> ProductVariantQueryset:
    return where_filter_qs(
        ProductVariant.objects.filter(id__in=variant_qs.values("id")),
        {},
        ProductVariantWhere,
        predicate_data,
        None,
    )


def _handle_collection_predicate(
    predicate_data: dict[str, Union[dict, list]], variant_qs: QuerySet[ProductVariant]
) -> ProductVariantQueryset:
    collection_products = CollectionProduct.objects.filter(
        product_id__in=variant_qs.values("product_id")
    )
    collection_qs = where_filter_qs(
        Collection.objects.filter(
            Exists(collection_products.filter(collection_id=OuterRef("id")))
        ),
        {},
        CollectionWhere,
        predicate_data,
        None,
    )
    collection_products = CollectionProduct.objects.filter(
        Exists(collection_qs.filter(id=OuterRef("collection_id")))
    )
    return ProductVariant.objects.filter(
        Exists(collection_products.filter(product_id=OuterRef("product_id")))
    )


def _handle_category_predicate(
    predicate_data: dict[str, Union[dict, list]], variant_qs
) -> ProductVariantQueryset:
    products = Product.objects.filter(id__in=variant_qs.values("product_id"))
    category_qs = where_filter_qs(
        Category.objects.filter(Exists(products.filter(category_id=OuterRef("id")))),
        {},
        CategoryWhere,
        predicate_data,
        None,
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


def get_variants_for_catalogue_predicate(
    predicate,
    queryset: Optional[ProductVariantQueryset] = None,
    database_connection_name: str = settings.DATABASE_CONNECTION_DEFAULT_NAME,
):
    if not predicate:
        return ProductVariant.objects.none()
    if queryset is None:
        queryset = ProductVariant.objects.using(database_connection_name).all()
    return filter_qs_by_predicate(predicate, queryset, PredicateObjectType.CATALOGUE)


def filter_qs_by_predicate(
    predicate: dict,
    base_qs: QuerySet,
    predicate_type: PredicateObjectType,
    currency: Optional[str] = None,
    *,
    result_qs: Optional[QuerySet] = None,
) -> QuerySet:
    """Filter QuerySet by predicate conditions.

    Args:
        predicate: dict with conditions
        result_qs: QuerySet that contains results of previous conditions
        base_qs: QuerySet that contains all objects that can be filtered
        predicate_type: type of predicate (catalogue or order)
        currency: currency used for filtering by order predicates
            with price conditions

    """
    if not predicate:
        return base_qs.model.objects.none()

    if result_qs is None:
        result_qs = base_qs

    result_qs = cast(QuerySet, result_qs)

    and_data: Optional[list[dict]] = predicate.pop("AND", None)
    or_data: Optional[list[dict]] = predicate.pop("OR", None)

    if and_data:
        result_qs = _handle_and_data(
            result_qs, base_qs, and_data, predicate_type, currency
        )
    if or_data:
        result_qs = _handle_or_data(
            result_qs, base_qs, or_data, predicate_type, currency
        )
    if predicate:
        result_qs = _handle_predicate(
            result_qs, base_qs, predicate, Operators.AND, predicate_type, currency
        )

    return result_qs


def _handle_and_data(
    result_qs: QuerySet,
    base_qs: QuerySet,
    data: PREDICATE_OPERATOR_DATA_T,
    predicate_type: PredicateObjectType,
    currency: Optional[str] = None,
) -> QuerySet:
    for predicate_data in data:
        if contains_filter_operator(predicate_data):
            result_qs &= filter_qs_by_predicate(
                predicate_data, base_qs, predicate_type, currency, result_qs=result_qs
            )
        else:
            result_qs = _handle_predicate(
                result_qs,
                base_qs,
                predicate_data,
                Operators.AND,
                predicate_type,
                currency,
            )
    return result_qs


def _handle_or_data(
    result_qs: QuerySet,
    base_qs: QuerySet,
    data: PREDICATE_OPERATOR_DATA_T,
    predicate_type: PredicateObjectType,
    currency: Optional[str] = None,
) -> QuerySet:
    qs = result_qs.model.objects.none()
    for predicate_data in data:
        if contains_filter_operator(predicate_data):
            qs |= filter_qs_by_predicate(
                predicate_data, base_qs, predicate_type, currency, result_qs=result_qs
            )
        else:
            qs = _handle_predicate(
                qs, base_qs, predicate_data, Operators.OR, predicate_type, currency
            )
    result_qs &= qs
    return result_qs


def contains_filter_operator(input: dict[str, Union[dict, str, list, bool]]) -> bool:
    return any([operator in input for operator in ["AND", "OR", "NOT"]])


def _handle_predicate(
    result_qs: QuerySet,
    base_qs: QuerySet,
    predicate_data: dict[str, Union[dict, str, list, bool]],
    operator: Operators,
    predicate_type: PredicateObjectType,
    currency: Optional[str] = None,
):
    if predicate_type == PredicateObjectType.CATALOGUE:
        return _handle_catalogue_predicate(result_qs, base_qs, predicate_data, operator)
    elif predicate_type == PredicateObjectType.CHECKOUT:
        return _handle_checkout_predicate(
            result_qs, base_qs, predicate_data, operator, currency
        )
    elif predicate_type == PredicateObjectType.ORDER:
        return _handle_order_predicate(
            result_qs, base_qs, predicate_data, operator, currency
        )


def _handle_catalogue_predicate(
    result_qs: QuerySet,
    base_qs: QuerySet,
    predicate_data: dict[str, Union[dict, str, list, bool]],
    operator,
) -> QuerySet[ProductVariant]:
    for field, handle_method in PREDICATE_TO_HANDLE_METHOD.items():
        if field_data := predicate_data.get(field):
            field_data = cast(dict[str, Union[dict, list]], field_data)
            if operator == Operators.AND:
                result_qs &= handle_method(field_data, base_qs)
            else:
                result_qs |= handle_method(field_data, base_qs)
    return result_qs


def _handle_checkout_predicate(
    result_qs: QuerySet,
    base_qs: QuerySet,
    predicate_data: dict[str, Union[dict, str, list, bool]],
    operator,
    currency: Optional[str] = None,
):
    predicate_data = _predicate_to_snake_case(predicate_data)
    if predicate := predicate_data.get("discounted_object_predicate"):
        checkouts = where_filter_qs(
            Checkout.objects.filter(pk__in=base_qs.values("pk")),
            {"currency": currency} if currency else {},
            CheckoutDiscountedObjectWhere,
            predicate,
            None,
        )
        if operator == Operators.AND:
            result_qs &= checkouts
        else:
            result_qs |= checkouts
    return result_qs


def _handle_order_predicate(
    result_qs: QuerySet,
    base_qs: QuerySet,
    predicate_data: dict[str, Union[dict, str, list, bool]],
    operator,
    currency: Optional[str] = None,
):
    predicate_data = _predicate_to_snake_case(predicate_data)
    if predicate := predicate_data.get("discounted_object_predicate"):
        orders = where_filter_qs(
            Order.objects.filter(pk__in=base_qs.values("pk")),
            {"currency": currency} if currency else {},
            OrderDiscountedObjectWhere,
            predicate,
            None,
        )
        if operator == Operators.AND:
            result_qs &= orders
        else:
            result_qs |= orders
    return result_qs


def _predicate_to_snake_case(obj: Any) -> Any:
    if isinstance(obj, dict):
        data = {}
        for key, value in obj.items():
            if key in ["AND", "OR"]:
                data[key] = _predicate_to_snake_case(value)
            elif key in ["eq", "oneOf"]:
                data[key] = value
            else:
                data[_predicate_to_snake_case(key)] = _predicate_to_snake_case(value)
        return data
    if isinstance(obj, list):
        return [_predicate_to_snake_case(item) for item in obj]
    if isinstance(obj, str):
        return to_snake_case(obj)
    return obj


def convert_migrated_sale_predicate_to_model_ids(
    catalogue_predicate,
) -> Optional[dict[str, list[int]]]:
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


CatalogueInfo = defaultdict[str, set[Union[int, str]]]
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
