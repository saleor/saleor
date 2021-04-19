import graphene
from django.core.exceptions import ValidationError

from ...core.permissions import PluginsPermissions
from ...plugins.error_codes import PluginErrorCode
from ..core.mutations import BaseMutation
from ..core.types.common import PluginError
from .resolvers import resolve_plugin
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
        channel = graphene.String(
            required=False,
            description="Slug of a channel for which the data should be modified.",
        )
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
        channel_slug = data.get("channel")
        data = data.get("input")
        manager = info.context.plugins
        plugin = manager.get_plugin(plugin_id, channel_slug)
        if not plugin:
            raise ValidationError(
                {
                    "id": ValidationError(
                        "Plugin doesn't exist.", code=PluginErrorCode.NOT_FOUND.value
                    )
                }
            )

        if plugin in manager.global_plugins and channel_slug:
            raise ValidationError(
                {
                    "id": ValidationError(
                        "Plugin doesn't support configuration per channel.",
                        code=PluginErrorCode.INVALID.value,
                    )
                }
            )
        elif plugin not in manager.global_plugins and not channel_slug:
            raise ValidationError(
                {
                    "id": ValidationError(
                        "Plugin requires to specify channel slug.",
                        code=PluginErrorCode.NOT_FOUND.value,
                    )
                }
            )
        manager.save_plugin_configuration(plugin_id, channel_slug, data)
        return PluginUpdate(plugin=resolve_plugin(plugin_id, manager))
