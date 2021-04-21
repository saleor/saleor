from typing import List, Optional

import graphene

from .types import Plugin


def filter_plugin_is_active(plugins: List[Plugin], is_active) -> List[Plugin]:
    filtered_plugins = []
    for plugin in plugins:
        if plugin.global_configuration:
            if plugin.global_configuration.active is is_active:
                filtered_plugins.append(plugin)
        elif any(
            [config.active is is_active for config in plugin.channel_configurations]
        ):
            filtered_plugins.append(plugin)
    return filtered_plugins


def filter_plugin_search(plugins: List[Plugin], value: Optional[str]) -> List[Plugin]:
    plugin_fields = ["name", "description"]
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
