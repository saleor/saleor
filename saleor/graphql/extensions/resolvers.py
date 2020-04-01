from ...extensions.base_plugin import BasePlugin
from ...extensions.manager import get_extensions_manager
from ...extensions.models import PluginConfiguration
from .filters import filter_plugin_search
from .sorters import PluginSortField


def resolve_plugin(info, plugin_name):
    manager = get_extensions_manager()
    plugin: BasePlugin = manager.get_plugin(plugin_name)
    if not plugin:
        return None
    return PluginConfiguration(
        id=plugin.PLUGIN_NAME,
        active=plugin.active,
        configuration=plugin.configuration,
        description=plugin.PLUGIN_DESCRIPTION,
        name=plugin.PLUGIN_NAME,
    )


def resolve_plugins(sort_by=None, **_kwargs):
    plugin_filter = _kwargs.get("filter", {})
    manager = get_extensions_manager()
    sort_field = (
        sort_by.get("field", PluginSortField.NAME) if sort_by else PluginSortField.NAME
    )
    sort_reverse = sort_by.get("direction", False) if sort_by else False
    if sort_field == PluginSortField.IS_ACTIVE:

        plugins = sorted(
            manager.plugins,
            key=lambda p: (not p.active if sort_reverse else p.active, p.PLUGIN_NAME),
        )
    else:
        plugins = sorted(manager.plugins, key=lambda p: p.PLUGIN_NAME)
        if sort_reverse:
            plugins = reversed(plugins)

    if "active" in plugin_filter:
        plugins = [
            plugin for plugin in plugins if plugin.active is plugin_filter["active"]
        ]
    search_query = plugin_filter.get("search", "").lower()
    plugins = filter_plugin_search(plugins, search_query)

    return [
        PluginConfiguration(
            id=plugin.PLUGIN_NAME,
            active=plugin.active,
            configuration=plugin.configuration,
            description=plugin.PLUGIN_DESCRIPTION,
            name=plugin.PLUGIN_NAME,
        )
        for plugin in plugins
    ]
