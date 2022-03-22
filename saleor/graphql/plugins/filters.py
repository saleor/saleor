from typing import List, Optional

import graphene

from ..channel.types import Channel
from ..core.types import NonNullList
from ..utils import get_nodes
from .enums import PluginConfigurationType
from .types import Plugin


def filter_plugin_status_in_channels(
    plugins: List[Plugin], status_in_channels: dict
) -> List[Plugin]:
    is_active = status_in_channels["active"]
    channels_id = status_in_channels["channels"]
    channels = get_nodes(channels_id, Channel)

    filtered_plugins = []
    for plugin in plugins:
        if plugin.global_configuration:
            if plugin.global_configuration.active is is_active:
                filtered_plugins.append(plugin)
        else:
            for channel in channels:
                if any(
                    [
                        (config.channel.id == channel.id and config.active is is_active)
                        for config in plugin.channel_configurations
                    ]
                ):
                    filtered_plugins.append(plugin)
                    break
    return filtered_plugins


def filter_plugin_by_type(plugins: List[Plugin], type):
    if type == PluginConfigurationType.GLOBAL:
        plugins = [plugin for plugin in plugins if plugin.global_configuration]
    else:
        plugins = [plugin for plugin in plugins if not plugin.global_configuration]
    return plugins


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


class PluginStatusInChannelsInput(graphene.InputObjectType):
    active = graphene.Argument(graphene.Boolean, required=True)
    channels = graphene.Argument(NonNullList(graphene.ID), required=True)


class PluginFilterInput(graphene.InputObjectType):
    status_in_channels = graphene.Argument(PluginStatusInChannelsInput)
    search = graphene.Argument(graphene.String)
    type = graphene.Argument(PluginConfigurationType)
