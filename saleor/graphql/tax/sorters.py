import graphene

from ..core.types import SortInputObjectType


class TaxClassSortField(graphene.Enum):
    NAME = ["name", "pk"]

    @property
    def description(self):
        if self.name in TaxClassSortField.__enum__._member_names_:
            sort_name = self.name.lower().replace("_", " ")
            return f"Sort tax classes by {sort_name}."
        raise ValueError(f"Unsupported enum value: {self.value}")


class TaxClassSortingInput(SortInputObjectType):
    class Meta:
        sort_enum = TaxClassSortField
        type_name = "tax classes"
