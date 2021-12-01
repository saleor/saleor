import graphene

from ...core.permissions import PluginsPermissions
from ...core.tracing import traced_resolver
from ..core.connection import create_connection_slice
from ..core.fields import ConnectionField
from ..decorators import permission_required
from .filters import PluginFilterInput
from .mutations import PluginUpdate
from .resolvers import resolve_plugin, resolve_plugins
from .sorters import PluginSortingInput
from .types import Plugin, PluginCountableConnection


class PluginsQueries(graphene.ObjectType):
    plugin = graphene.Field(
        Plugin,
        id=graphene.Argument(
            graphene.ID, description="ID of the plugin.", required=True
        ),
        description="Look up a plugin by ID.",
    )

    plugins = ConnectionField(
        PluginCountableConnection,
        filter=PluginFilterInput(description="Filtering options for plugins."),
        sort_by=PluginSortingInput(description="Sort plugins."),
        description="List of plugins.",
    )

    @permission_required(PluginsPermissions.MANAGE_PLUGINS)
    @traced_resolver
    def resolve_plugin(self, info, **data):
        return resolve_plugin(data.get("id"), info.context.plugins)

    @permission_required(PluginsPermissions.MANAGE_PLUGINS)
    @traced_resolver
    def resolve_plugins(self, info, **kwargs):
        qs = resolve_plugins(info.context.plugins, **kwargs)
        return create_connection_slice(qs, info, kwargs, PluginCountableConnection)


class PluginsMutations(graphene.ObjectType):
    plugin_update = PluginUpdate.Field()
