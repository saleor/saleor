import graphene

from ..core.doc_category import DOC_CATEGORY_PRODUCTS
from ..core.types import SortInputObjectType
from ..directives import doc


@doc(category=DOC_CATEGORY_PRODUCTS)
class WarehouseSortField(graphene.Enum):
    NAME = ["name", "slug"]

    @property
    def description(self):
        if self.name in WarehouseSortField.__enum__._member_names_:
            sort_name = self.name.lower().replace("_", " ")
            return f"Sort warehouses by {sort_name}."
        raise ValueError(f"Unsupported enum value: {self.value}")


@doc(category=DOC_CATEGORY_PRODUCTS)
class WarehouseSortingInput(SortInputObjectType):
    class Meta:
        sort_enum = WarehouseSortField
        type_name = "warehouses"
