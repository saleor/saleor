import graphene

from ..core.types import SortInputObjectType


class AppSortField(graphene.Enum):
    NAME = ["name", "pk"]
    CREATION_DATE = ["created", "name", "pk"]

    @property
    def description(self):
        if self.name in AppSortField.__enum__._member_names_:
            sort_name = self.name.lower().replace("_", " ")
            return f"Sort apps by {sort_name}."
        raise ValueError("Unsupported enum value: %s" % self.value)


class AppSortingInput(SortInputObjectType):
    class Meta:
        sort_enum = AppSortField
        type_name = "apps"
