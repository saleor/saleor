import graphene

from ..core.types import SortInputObjectType


class WarehouseSortField(graphene.Enum):
    NAME = ["name", "slug"]

    @property
    def description(self):
        if self.name in WarehouseSortField.__enum__._member_names_:
            sort_name = self.name.lower().replace("_", " ")
            return f"Sort warehouses by {sort_name}."
        raise ValueError("Unsupported enum value: %s" % self.value)


class WarehouseSortingInput(SortInputObjectType):
    class Meta:
        sort_enum = WarehouseSortField
        type_name = "warehouses"
