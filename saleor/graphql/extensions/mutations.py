import graphene

from django.core.exceptions import ValidationError

from ...core.permissions import ExtensionsPermissions
from ...extensions.manager import get_extensions_manager
from ..core.mutations import BaseMutation
from ..core.types.common import ExtensionsError
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
        permissions = (ExtensionsPermissions.MANAGE_PLUGINS,)
        error_type_class = ExtensionsError
        error_type_field = "extensions_errors"

    @classmethod
    def perform_mutation(cls, root, info, **data):
        plugin_id = data.get("id")
        data = data.get("input")
        manager = get_extensions_manager()
        plugin = manager.get_plugin(plugin_id)
        if not plugin:
            raise ValidationError(
                {"id": ValidationError("Plugin doesn't exist", code="not_found")}
            )
        instance = manager.save_plugin_configuration(plugin_id, data)
        return PluginUpdate(plugin=instance)
