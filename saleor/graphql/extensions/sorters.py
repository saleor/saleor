import graphene

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


class PluginSortingInput(SortInputObjectType):
    class Meta:
        sort_enum = PluginSortField
        type_name = "plugins"
