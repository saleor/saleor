from collections import defaultdict

import graphene

from saleor.discount.utils import CatalogueInfo
from saleor.graphql.discount.mutations.sale_base_discount_catalogue import (
    NodeCatalogueInfo,
)


def convert_catalogue_info_to_global_ids(
    catalogue_info: CatalogueInfo,
) -> NodeCatalogueInfo:
    catalogue_fields = ["categories", "collections", "products", "variants"]
    type_names = ["Category", "Collection", "Product", "ProductVariant"]
    converted_catalogue_info: NodeCatalogueInfo = defaultdict(set)

    for type_name, catalogue_field in zip(type_names, catalogue_fields):
        converted_catalogue_info[catalogue_field].update(
            graphene.Node.to_global_id(type_name, id_)
            for id_ in catalogue_info[catalogue_field]
        )
    return converted_catalogue_info
