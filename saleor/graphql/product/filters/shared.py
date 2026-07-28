import graphene

from ...core.doc_category import DOC_CATEGORY_PRODUCTS
from ...core.types import BaseInputObjectType, IntRangeInput, NonNullList
from ...utils.filters import filter_range_field


def filter_updated_at_range(qs, _, value):
    return filter_range_field(qs, "updated_at", value)


class ProductStockFilterInput(BaseInputObjectType):
    warehouse_ids = NonNullList(graphene.ID, required=False)
    quantity = graphene.Field(IntRangeInput, required=False)

    class Meta:
        doc_category = DOC_CATEGORY_PRODUCTS
