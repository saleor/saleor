import graphene

from ...extensions.manager import get_extensions_manager
from ..core.mutations import BaseMutation
from .types import PluginConfiguration


class ConfigurationItemInput(graphene.InputObjectType):
    name = graphene.String(required=True, description="Name of the field to update")
    value = graphene.String(required=True, description="Value of the given ")


class PluginConfigurationUpdateInput(graphene.InputObjectType):
    active = graphene.Boolean(
        required=False, description="Indicates whether the plugin should be enabled"
    )
    configuration = graphene.List(
        ConfigurationItemInput,
        required=False,
        description="Configuration of the plugin",
    )


class PluginConfigurationUpdate(BaseMutation):
    plugin_configuration = graphene.Field(PluginConfiguration)

    class Arguments:
        id = graphene.ID(required=True, description="ID of plugin to update")
        input = PluginConfigurationUpdateInput(
            description="Fields required to update a plugin configuration.",
            required=True,
        )

    class Meta:
        description = "Update plugin configuration"
        permissions = "extensions.manage_plugins"

    @classmethod
    def perform_mutation(cls, root, info, **data):
        plugin_id = data.get("id")
        input = data.get("input")
        instance = cls.get_node_or_error(info, plugin_id, only_type=PluginConfiguration)
        manager = get_extensions_manager()
        instance = manager.save_plugin_configuration(instance.name, input)
        return PluginConfigurationUpdate(plugin_configuration=instance)
