import graphene

from ...core.permissions import ExtensionsPermissions
from ..core.fields import FilterInputConnectionField
from ..decorators import permission_required
from .filters import PluginFilterInput
from .mutations import PluginUpdate
from .resolvers import resolve_plugin, resolve_plugins
from .sorters import PluginSortingInput
from .types import Plugin


class ExtensionsQueries(graphene.ObjectType):
    plugin = graphene.Field(
        Plugin,
        id=graphene.Argument(
            graphene.ID, description="ID of the plugin.", required=True
        ),
        description="Look up a plugin by ID.",
    )
    plugins = FilterInputConnectionField(
        Plugin,
        filter=PluginFilterInput(description="Filtering options for plugins."),
        sort_by=PluginSortingInput(description="Sort plugins."),
        description="List of plugins.",
    )

    @permission_required(ExtensionsPermissions.MANAGE_PLUGINS)
    def resolve_plugin(self, info, **data):
        return resolve_plugin(info, data.get("id"))

    @permission_required(ExtensionsPermissions.MANAGE_PLUGINS)
    def resolve_plugins(self, _info, **kwargs):
        return resolve_plugins(**kwargs)


class ExtensionsMutations(graphene.ObjectType):
    plugin_update = PluginUpdate.Field()
