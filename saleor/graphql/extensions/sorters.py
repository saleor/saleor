import graphene
from django.db.models import QuerySet

from ..core.types import SortInputObjectType


class PluginSortField(graphene.Enum):
    NAME = "name"
    IS_ACTIVE = "active"

    @property
    def description(self):
        # pylint: disable=no-member
        descriptions = {
            PluginSortField.NAME.name: "name",
            PluginSortField.ACTIVE.name: "activity status",
        }
        if self.name in descriptions:
            return f"Sort plugins by {descriptions[self.name]}."
        raise ValueError("Unsupported enum value: %s" % self.value)

    @staticmethod
    def sort_by_active(queryset: QuerySet, sort_by: SortInputObjectType) -> QuerySet:
        return queryset.order_by(f"{sort_by.direction}{sort_by.field}", "name")


class PluginSortingInput(SortInputObjectType):
    class Meta:
        sort_enum = PluginSortField
        type_name = "plugins"
