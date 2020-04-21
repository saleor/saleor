import graphene

from ...core.permissions import PluginsPermissions
from ..core.fields import BaseDjangoConnectionField
from ..decorators import permission_required
from .filters import PluginFilterInput
from .mutations import PluginUpdate
from .resolvers import resolve_plugin, resolve_plugins
from .sorters import PluginSortingInput
from .types import Plugin


class PluginsQueries(graphene.ObjectType):
    plugin = graphene.Field(
        Plugin,
        id=graphene.Argument(
            graphene.ID, description="ID of the plugin.", required=True
        ),
        description="Look up a plugin by ID.",
    )
    plugins = BaseDjangoConnectionField(
        Plugin,
        filter=PluginFilterInput(description="Filtering options for plugins."),
        sort_by=PluginSortingInput(description="Sort plugins."),
        description="List of plugins.",
    )

    @permission_required(PluginsPermissions.MANAGE_PLUGINS)
    def resolve_plugin(self, info, **data):
        return resolve_plugin(info, data.get("id"))

    @permission_required(PluginsPermissions.MANAGE_PLUGINS)
    def resolve_plugins(self, _info, **kwargs):
        return resolve_plugins(**kwargs)


class PluginsMutations(graphene.ObjectType):
    plugin_update = PluginUpdate.Field()
