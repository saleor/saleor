from collections import defaultdict
from typing import DefaultDict, Set, Union

CatalogueInfo = DefaultDict[str, Set[Union[int, str]]]
PREDICATE_TO_CATALOGUE_INFO_MAP = {
    "collectionPredicate": "collections",
    "categoryPredicate": "categories",
    "productPredicate": "products",
    "variantPredicate": "variants",
}


def convert_migrated_sale_predicate_to_catalogue_info(
    catalogue_predicate,
) -> CatalogueInfo:
    catalogue_info: CatalogueInfo = defaultdict(set)
    for field in PREDICATE_TO_CATALOGUE_INFO_MAP.values():
        catalogue_info[field] = set()

    if catalogue_predicate.get("OR"):
        predicates = {
            next(item.keys()): next(item.values())["ids"]
            for item in catalogue_predicate["OR"]
        }
        for predicate_name, field in PREDICATE_TO_CATALOGUE_INFO_MAP.items():
            catalogue_info[field] = set(predicates.get(predicate_name, {}))

    return catalogue_info
