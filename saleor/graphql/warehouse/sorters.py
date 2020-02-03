import graphene

from ..core.types import SortInputObjectType


class WarehouseSortField(graphene.Enum):
    NAME = "name"

    @property
    def description(self):
        # pylint: disable=no-member
        if self in [
            WarehouseSortField.NAME,
        ]:
            sort_name = self.name.lower().replace("_", " ")
            return f"Sort warehouses by {sort_name}."
        raise ValueError("Unsupported enum value: %s" % self.value)


class WarehouseSortingInput(SortInputObjectType):
    class Meta:
        sort_enum = WarehouseSortField
        type_name = "warehouses"
