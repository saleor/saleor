from ...extensions.base_plugin import BasePlugin
from ...extensions.manager import get_extensions_manager
from .sorters import PluginSortField


def resolve_plugin(info, plugin_global_id):
    manager = get_extensions_manager()
    plugin: BasePlugin = manager.get_plugin(plugin_global_id)
    if not plugin:
        return None
    return {
        "id": plugin.PLUGIN_NAME,
        "active": plugin.active,
        "configuration": plugin.configuration,
        "description": plugin.PLUGIN_DESCRIPTION,
        "name": plugin.PLUGIN_NAME,
    }


def resolve_plugins(sort_by=None, **_kwargs):
    manager = get_extensions_manager()
    sort_field = (
        sort_by.get("field", PluginSortField.NAME) if sort_by else PluginSortField.NAME
    )
    sort_reverse = sort_by.get("reverse", False) if sort_by else False
    if sort_field == PluginSortField.IS_ACTIVE:
        plugins = sorted(manager.plugins, key=lambda p: (p.active, p.PLUGIN_NAME))
    else:
        plugins = sorted(manager.plugins, key=lambda p: p.PLUGIN_NAME)
    if sort_reverse:
        plugins = reversed(plugins)
    return [
        {
            "id": plugin.PLUGIN_NAME,
            "active": plugin.active,
            "configuration": plugin.configuration,
            "description": plugin.PLUGIN_DESCRIPTION,
            "name": plugin.PLUGIN_NAME,
        }
        for plugin in plugins
    ]
