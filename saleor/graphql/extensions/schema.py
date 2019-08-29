import graphene
from graphql_jwt.decorators import permission_required

from ..core.fields import PrefetchingConnectionField
from .mutations import PluginUpdate
from .resolvers import resolve_plugin, resolve_plugins
from .types import Plugin


class ExtensionsQueries(graphene.ObjectType):
    plugin = graphene.Field(
        Plugin,
        id=graphene.Argument(graphene.ID, required=True),
        description="Lookup a plugin by ID.",
    )
    plugins = PrefetchingConnectionField(Plugin, description="List of plugins")

    @permission_required("extensions.manage_plugins")
    def resolve_plugin(self, info, **data):
        return resolve_plugin(info, data.get("id"))

    @permission_required("extensions.manage_plugins")
    def resolve_plugins(self, _info, **_kwargs):
        return resolve_plugins()


class ExtensionsMutations(graphene.ObjectType):
    plugin_update = PluginUpdate.Field()
