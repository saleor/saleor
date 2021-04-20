from ...core.tracing import traced_resolver
from ...plugins.base_plugin import BasePlugin
from ...plugins.models import PluginConfiguration
from .filters import filter_plugin_search
from .sorters import sort_plugins


@traced_resolver
def resolve_plugin(info, plugin_id, manager):
    plugin: BasePlugin = manager.get_plugin(plugin_id)
    if not plugin:
        return None
    return PluginConfiguration(
        id=plugin.PLUGIN_ID,
        identifier=plugin.PLUGIN_ID,
        active=plugin.active,
        configuration=plugin.configuration,
        description=plugin.PLUGIN_DESCRIPTION,
        name=plugin.PLUGIN_NAME,
    )


def resolve_plugins(manager, sort_by=None, **kwargs):
    plugin_filter = kwargs.get("filter", {})
    search_query = plugin_filter.get("search")
    filter_active = plugin_filter.get("active")

    plugins = manager.plugins

    if filter_active is not None:
        plugins = [plugin for plugin in plugins if plugin.active is filter_active]

    plugins = filter_plugin_search(plugins, search_query)
    plugins = sort_plugins(plugins, sort_by)

    return [
        PluginConfiguration(
            id=plugin.PLUGIN_ID,
            identifier=plugin.PLUGIN_ID,
            active=plugin.active,
            configuration=plugin.configuration,
            description=plugin.PLUGIN_DESCRIPTION,
            name=plugin.PLUGIN_NAME,
        )
        for plugin in plugins
    ]
