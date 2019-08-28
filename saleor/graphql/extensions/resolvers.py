import graphene

from ...extensions.manager import get_extensions_manager
from .types import Plugin


def resolve_plugin(info, plugin_global_id):
    manager = get_extensions_manager()
    plugin = graphene.Node.get_node_from_global_id(info, plugin_global_id, Plugin)
    if not plugin:
        return None
    return manager.get_plugin_configuration(plugin.name)


def resolve_plugins():
    manager = get_extensions_manager()
    return manager.get_plugin_configurations()
