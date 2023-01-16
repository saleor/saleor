import graphene

from ...core.permissions import PluginsPermissions
from ..core import ResolveInfo
from ..core.connection import create_connection_slice
from ..core.fields import ConnectionField, PermissionsField
from ..core.tracing import traced_resolver
from .dataloaders import plugin_manager_promise_callback
from .filters import PluginFilterInput
from .mutations import PluginUpdate
from .resolvers import resolve_plugin, resolve_plugins
from .sorters import PluginSortingInput
from .types import Plugin, PluginCountableConnection


class PluginsQueries(graphene.ObjectType):
    plugin = PermissionsField(
        Plugin,
        id=graphene.Argument(
            graphene.ID, description="ID of the plugin.", required=True
        ),
        description="Look up a plugin by ID.",
        permissions=[
            PluginsPermissions.MANAGE_PLUGINS,
        ],
    )

    plugins = ConnectionField(
        PluginCountableConnection,
        filter=PluginFilterInput(description="Filtering options for plugins."),
        sort_by=PluginSortingInput(description="Sort plugins."),
        description="List of plugins.",
        permissions=[
            PluginsPermissions.MANAGE_PLUGINS,
        ],
    )

    @staticmethod
    @traced_resolver
    @plugin_manager_promise_callback
    def resolve_plugin(_root, _info: ResolveInfo, manager, **data):
        return resolve_plugin(data.get("id"), manager)

    @staticmethod
    @traced_resolver
    @plugin_manager_promise_callback
    def resolve_plugins(_root, info: ResolveInfo, manager, **kwargs):
        qs = resolve_plugins(manager, **kwargs)
        return create_connection_slice(qs, info, kwargs, PluginCountableConnection)


class PluginsMutations(graphene.ObjectType):
    plugin_update = PluginUpdate.Field()
