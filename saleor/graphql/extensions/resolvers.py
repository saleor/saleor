import graphene

from ...extensions.manager import get_extensions_manager
from ..utils import sort_queryset
from .sorters import PluginSortField
from .types import Plugin


def resolve_plugin(info, plugin_global_id):
    manager = get_extensions_manager()
    plugin = graphene.Node.get_node_from_global_id(info, plugin_global_id, Plugin)
    if not plugin:
        return None
    return manager.get_plugin_configuration(plugin.name)


def resolve_plugins(sort_by=None, **_kwargs):
    manager = get_extensions_manager()
    qs = manager.get_plugin_configurations()
    qs = sort_queryset(qs, sort_by, PluginSortField)
    return qs
