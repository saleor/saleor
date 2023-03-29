from ..core.doc_category import DOC_CATEGORY_PRODUCTS
from ..core.types import BaseEnum, SortInputObjectType


class WarehouseSortField(BaseEnum):
    NAME = ["name", "slug"]

    class Meta:
        doc_category = DOC_CATEGORY_PRODUCTS

    @property
    def description(self):
        if self.name in WarehouseSortField.__enum__._member_names_:
            sort_name = self.name.lower().replace("_", " ")
            return f"Sort warehouses by {sort_name}."
        raise ValueError(f"Unsupported enum value: {self.value}")


class WarehouseSortingInput(SortInputObjectType):
    class Meta:
        doc_category = DOC_CATEGORY_PRODUCTS
        sort_enum = WarehouseSortField
        type_name = "warehouses"
