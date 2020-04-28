from typing import TYPE_CHECKING, List, Optional

import graphene

from ..core.types import SortInputObjectType

if TYPE_CHECKING:
    # flake8: noqa
    from ...plugins.base_plugin import BasePlugin


def sort_plugins(
    plugins: List["BasePlugin"], sort_by: Optional[dict]
) -> List["BasePlugin"]:
    sort_reverse = sort_by.get("direction", False) if sort_by else False
    sort_field = (
        sort_by.get("field", PluginSortField.NAME) if sort_by else PluginSortField.NAME
    )
    if sort_field == PluginSortField.IS_ACTIVE:
        plugins = sorted(
            plugins,
            key=lambda p: (not p.active if sort_reverse else p.active, p.PLUGIN_ID),
        )
    else:
        plugins = sorted(plugins, key=lambda p: p.PLUGIN_ID)
        if sort_reverse:
            plugins = list(reversed(plugins))
    return plugins


class PluginSortField(graphene.Enum):
    NAME = ["name"]
    IS_ACTIVE = ["active", "name"]

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
