from collections import defaultdict

import graphene

from ....discount.models import Promotion
from ....discount.utils import CatalogueInfo

CATALOGUE_FIELD_TO_TYPE_NAME = {
    "categories": "Category",
    "collections": "Collection",
    "products": "Product",
    "variants": "ProductVariant",
}


def convert_catalogue_info_to_global_ids(
    catalogue_info: CatalogueInfo,
) -> defaultdict[str, set[str]]:
    converted_catalogue_info: defaultdict[str, set[str]] = defaultdict(set)

    for catalogue_field, type_name in CATALOGUE_FIELD_TO_TYPE_NAME.items():
        converted_catalogue_info[catalogue_field].update(
            graphene.Node.to_global_id(type_name, id_)
            for id_ in catalogue_info[catalogue_field]
        )
    return converted_catalogue_info


def clear_promotion_old_sale_id(promotion: Promotion, *, save=False):
    """Clear the promotion `old_sale_id` if set."""
    if promotion.old_sale_id:
        promotion.old_sale_id = None
        if save:
            promotion.save(update_fields=["old_sale_id"])
