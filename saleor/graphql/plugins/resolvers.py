from collections import defaultdict
from typing import Dict, List, Tuple

from ...plugins.base_plugin import BasePlugin, ConfigurationTypeField
from .filters import filter_plugin_search
from .sorters import sort_plugins
from .types import Plugin


def hide_private_configuration_fields(configuration, config_structure):
    if not config_structure:
        return

    for field in configuration:
        name = field["name"]
        value = field["value"]
        if value is None:
            continue
        field_type = config_structure.get(name, {}).get("type")
        if field_type == ConfigurationTypeField.PASSWORD:
            field["value"] = "" if value else None

        if field_type in [
            ConfigurationTypeField.SECRET,
            ConfigurationTypeField.SECRET_MULTILINE,
        ]:
            if not value:
                field["value"] = None
            elif len(value) > 4:
                field["value"] = value[-4:]
            else:
                field["value"] = value[-1:]


def aggregate_plugins_configuration(
    manager,
) -> Tuple[Dict[str, BasePlugin], Dict[str, List[BasePlugin]]]:
    plugins_per_channel: Dict[str, List[BasePlugin]] = defaultdict(list)
    global_plugins: Dict[str, BasePlugin] = {}

    for plugin in manager.all_plugins:
        hide_private_configuration_fields(plugin.configuration, plugin.CONFIG_STRUCTURE)
        if not getattr(plugin, "CONFIGURATION_PER_CHANNEL", False):
            global_plugins[plugin.PLUGIN_ID] = plugin
        else:
            plugins_per_channel[plugin.PLUGIN_ID].append(plugin)
    return global_plugins, plugins_per_channel


def resolve_plugin(plugin_id, manager):
    global_plugins, plugins_per_channel = aggregate_plugins_configuration(manager)
    plugin: BasePlugin = manager.get_plugin(plugin_id)
    if not plugin:
        return None
    return Plugin(
        id=plugin.PLUGIN_ID,
        global_configuration=global_plugins.get(plugin.PLUGIN_ID),
        channel_configurations=plugins_per_channel.get(plugin.PLUGIN_ID),
        description=plugin.PLUGIN_DESCRIPTION,
        name=plugin.PLUGIN_NAME,
    )


def resolve_plugins(manager, sort_by=None, **kwargs):
    global_configs, configs_per_channel = aggregate_plugins_configuration(manager)
    plugin_filter = kwargs.get("filter", {})
    search_query = plugin_filter.get("search")
    filter_active = plugin_filter.get("active")

    plugins = manager.all_plugins

    if filter_active is not None:
        plugins = [plugin for plugin in plugins if plugin.active is filter_active]

    plugins = filter_plugin_search(plugins, search_query)
    plugins = sort_plugins(plugins, sort_by)

    return [
        Plugin(
            id=plugin.PLUGIN_ID,
            global_configuration=global_configs.get(plugin.PLUGIN_ID),
            channel_configurations=configs_per_channel.get(plugin.PLUGIN_ID),
            description=plugin.PLUGIN_DESCRIPTION,
            name=plugin.PLUGIN_NAME,
        )
        for plugin in plugins
    ]
