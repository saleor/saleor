import graphene

from ..core.types import SortInputObjectType


class TaxConfigurationSortField(graphene.Enum):
    CHANNEL = ["channel"]

    @property
    def description(self):
        if self.name in TaxConfigurationSortField.__enum__._member_names_:
            sort_name = self.name.lower().replace("_", " ")
            return f"Sort tax configurations by {sort_name}."
        raise ValueError(f"Unsupported enum value: {self.value}")


class TaxConfigurationSortingInput(SortInputObjectType):
    class Meta:
        sort_enum = TaxConfigurationSortField
        type_name = "tax configurations"
