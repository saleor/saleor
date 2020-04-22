import graphene

from ..core.types import SortInputObjectType


class AppSortField(graphene.Enum):
    NAME = ["name", "pk"]
    CREATION_DATE = ["created", "name", "pk"]

    @property
    def description(self):
        # pylint: disable=no-member
        if self in [
            AppSortField.NAME,
            AppSortField.CREATION_DATE,
        ]:
            sort_name = self.name.lower().replace("_", " ")
            return f"Sort apps by {sort_name}."
        raise ValueError("Unsupported enum value: %s" % self.value)


class AppSortingInput(SortInputObjectType):
    class Meta:
        sort_enum = AppSortField
        type_name = "apps"
