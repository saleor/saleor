from django.db.models import Exists, OuterRef

from ....attribute import models
from ....page import models as page_models
from ....product import models as product_models


def get_product_ids_to_search_index_update_for_attribute_values(
    values: list[models.AttributeValue],
) -> list[int]:
    """Get product IDs that need search index updates when attribute values are changed.

    Finds all products that has the given attribute values assigned or their variants
    have the given attribute values assigned.
    """
    if not values:
        return []
    assigned_variant_values = models.AssignedVariantAttributeValue.objects.filter(
        value_id__in=[v.id for v in values]
    )
    assigned_attributes = models.AssignedVariantAttribute.objects.filter(
        Exists(assigned_variant_values.filter(assignment_id=OuterRef("id")))
    )
    variants = product_models.ProductVariant.objects.filter(
        Exists(assigned_attributes.filter(variant_id=OuterRef("id")))
    )
    assigned_product_values = models.AssignedProductAttributeValue.objects.filter(
        value_id__in=[v.id for v in values]
    )
    product_ids = product_models.Product.objects.filter(
        Exists(assigned_product_values.filter(product_id=OuterRef("id")))
        | Exists(variants.filter(product_id=OuterRef("id")))
    ).values_list("id", flat=True)
    return list(product_ids)


def get_page_ids_to_search_index_update_for_attribute_values(
    values: list[models.AttributeValue],
) -> list[int]:
    """Get page IDs that need search index updates when attribute values are changed.

    Finds all pages that has the given attribute values assigned.
    """
    if not values:
        return []
    assigned_values = models.AssignedPageAttributeValue.objects.filter(
        value_id__in=[v.id for v in values]
    )
    page_ids = page_models.Page.objects.filter(
        Exists(assigned_values.filter(page_id=OuterRef("id")))
    ).values_list("id", flat=True)
    return list(page_ids)
