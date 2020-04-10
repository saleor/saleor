import graphene
from django.core.exceptions import ValidationError

from ...core.permissions import PluginsPermissions
from ...plugins.error_codes import PluginErrorCode
from ...plugins.manager import get_plugins_manager
from ..core.mutations import BaseMutation
from ..core.types.common import PluginError
from .types import Plugin


class ConfigurationItemInput(graphene.InputObjectType):
    name = graphene.String(required=True, description="Name of the field to update.")
    value = graphene.String(
        required=False, description="Value of the given field to update."
    )


class PluginUpdateInput(graphene.InputObjectType):
    active = graphene.Boolean(
        required=False, description="Indicates whether the plugin should be enabled."
    )
    configuration = graphene.List(
        ConfigurationItemInput,
        required=False,
        description="Configuration of the plugin.",
    )


class PluginUpdate(BaseMutation):
    plugin = graphene.Field(Plugin)

    class Arguments:
        id = graphene.ID(required=True, description="ID of plugin to update.")
        input = PluginUpdateInput(
            description="Fields required to update a plugin configuration.",
            required=True,
        )

    class Meta:
        description = "Update plugin configuration."
        permissions = (PluginsPermissions.MANAGE_PLUGINS,)
        error_type_class = PluginError
        error_type_field = "plugins_errors"

    @classmethod
    def perform_mutation(cls, root, info, **data):
        plugin_id = data.get("id")
        data = data.get("input")
        manager = get_plugins_manager()
        plugin = manager.get_plugin(plugin_id)
        if not plugin:
            raise ValidationError(
                {
                    "id": ValidationError(
                        "Plugin doesn't exist", code=PluginErrorCode.NOT_FOUND
                    )
                }
            )
        instance = manager.save_plugin_configuration(plugin_id, data)
        return PluginUpdate(plugin=instance)
