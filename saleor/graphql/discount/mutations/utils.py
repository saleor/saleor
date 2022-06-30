from collections import defaultdict
from typing import DefaultDict, Set

import graphene

from ....discount.utils import CatalogueInfo


def convert_catalogue_info_to_global_ids(
    catalogue_info: CatalogueInfo,
) -> DefaultDict[str, Set[str]]:
    catalogue_fields = ["categories", "collections", "products", "variants"]
    type_names = ["Category", "Collection", "Product", "ProductVariant"]
    converted_catalogue_info: DefaultDict[str, Set[str]] = defaultdict(set)

    for type_name, catalogue_field in zip(type_names, catalogue_fields):
        converted_catalogue_info[catalogue_field].update(
            graphene.Node.to_global_id(type_name, id_)
            for id_ in catalogue_info[catalogue_field]
        )
    return converted_catalogue_info
