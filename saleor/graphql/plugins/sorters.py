from typing import Optional

import graphene

from ..core.enums import OrderDirection
from ..core.types import SortInputObjectType
from .types import Plugin


def sort_active_key(plugin: Plugin, sort_reverse: bool):
    if plugin.global_configuration:
        active = plugin.global_configuration.active
        name = plugin.name
    else:
        active = False
        if any(
            [configuration.active for configuration in plugin.channel_configurations]
        ):
            active = True
        name = plugin.name
    return not active if sort_reverse else active, name


def sort_plugins(plugins: list["Plugin"], sort_by: Optional[dict]) -> list["Plugin"]:
    sort_reverse = False
    direction = sort_by.get("direction", OrderDirection.ASC) if sort_by else None
    if direction == OrderDirection.DESC:
        sort_reverse = True

    sort_field = (
        sort_by.get("field", PluginSortField.NAME) if sort_by else PluginSortField.NAME
    )

    if sort_field == PluginSortField.IS_ACTIVE:
        plugins = sorted(
            plugins,
            key=lambda p: sort_active_key(p, sort_reverse),
        )
    else:
        plugins = sorted(plugins, key=lambda p: p.name, reverse=sort_reverse)
    return plugins


class PluginSortField(graphene.Enum):
    NAME = ["name"]
    IS_ACTIVE = ["active", "name"]

    @property
    def description(self):
        # pylint: disable=no-member
        descriptions = {
            PluginSortField.NAME.name: "name",  # type: ignore[attr-defined]
            PluginSortField.ACTIVE.name: "activity status",
        }
        if self.name in descriptions:
            return f"Sort plugins by {descriptions[self.name]}."
        raise ValueError(f"Unsupported enum value: {self.value}")


class PluginSortingInput(SortInputObjectType):
    class Meta:
        sort_enum = PluginSortField
        type_name = "plugins"
