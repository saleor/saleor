import graphene
from graphql_jwt.decorators import permission_required

from ..core.fields import PrefetchingConnectionField
from .resolvers import resolve_plugin_configuration, resolve_plugin_configurations
from .types import PluginConfiguration


class ExtensionsQueries(graphene.ObjectType):
    plugin_configuration = graphene.Field(
        PluginConfiguration,
        id=graphene.Argument(graphene.ID, required=True),
        description="Lookup a plugin configuration by ID.",
    )
    plugin_configurations = PrefetchingConnectionField(
        PluginConfiguration, description="List of plugin configuration"
    )

    @permission_required("giftcard.manage_gift_card")
    def resolve_plugin_configuration(self, info, **data):
        return resolve_plugin_configuration(info, data.get("id"))

    @permission_required("giftcard.manage_gift_card")
    def resolve_plugin_configurations(self, _info, **_kwargs):
        return resolve_plugin_configurations()
