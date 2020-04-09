from typing import TYPE_CHECKING, List, Optional

import graphene

if TYPE_CHECKING:
    # flake8: noqa
    from ...plugins.base_plugin import BasePlugin


def filter_plugin_search(
    plugins: List["BasePlugin"], value: Optional[str]
) -> List["BasePlugin"]:
    plugin_fields = ["PLUGIN_NAME", "PLUGIN_DESCRIPTION"]
    if value is not None:
        return [
            plugin
            for plugin in plugins
            if any(
                [
                    value.lower() in getattr(plugin, field).lower()
                    for field in plugin_fields
                ]
            )
        ]
    return plugins


class PluginFilterInput(graphene.InputObjectType):
    active = graphene.Argument(graphene.Boolean)
    search = graphene.Argument(graphene.String)
