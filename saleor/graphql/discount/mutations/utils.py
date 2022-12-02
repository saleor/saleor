from collections import defaultdict
from typing import DefaultDict, Set

import graphene

from ....discount.utils import CatalogueInfo

CATALOGUE_FIELD_TO_TYPE_NAME = {
    "categories": "Category",
    "collections": "Collection",
    "products": "Product",
    "variants": "ProductVariant",
}


def convert_catalogue_info_to_global_ids(
    catalogue_info: CatalogueInfo,
) -> DefaultDict[str, Set[str]]:
    converted_catalogue_info: DefaultDict[str, Set[str]] = defaultdict(set)

    for catalogue_field, type_name in CATALOGUE_FIELD_TO_TYPE_NAME.items():
        converted_catalogue_info[catalogue_field].update(
            graphene.Node.to_global_id(type_name, id_)
            for id_ in catalogue_info[catalogue_field]
        )
    return converted_catalogue_info
