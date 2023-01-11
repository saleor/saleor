import graphene
from django.core.exceptions import ValidationError

from ...core.permissions import PluginsPermissions
from ...plugins.error_codes import PluginErrorCode
from ...plugins.manager import get_plugins_manager
from ..channel.types import Channel
from ..core import ResolveInfo
from ..core.mutations import BaseMutation
from ..core.types import NonNullList, PluginError
from .dataloaders import get_plugin_manager_promise
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
    configuration = NonNullList(
        ConfigurationItemInput,
        required=False,
        description="Configuration of the plugin.",
    )


class PluginUpdate(BaseMutation):
    plugin = graphene.Field(Plugin)

    class Arguments:
        id = graphene.ID(required=True, description="ID of plugin to update.")
        channel_id = graphene.ID(
            required=False,
            description="ID of a channel for which the data should be modified.",
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
    def clean_input(cls, info: ResolveInfo, data):
        plugin_id = data.get("id")
        channel_id = data.get("channel_id")
        channel = None
        if channel_id:
            channel = cls.get_node_or_error(info, channel_id, only_type=Channel)

        channel_slug = channel.slug if channel else None
        input_data = data.get("input")

        manager = get_plugin_manager_promise(info.context).get()
        plugin = manager.get_plugin(plugin_id, channel_slug)
        if not plugin or plugin.HIDDEN is True:
            raise ValidationError(
                {
                    "id": ValidationError(
                        "Plugin doesn't exist.", code=PluginErrorCode.NOT_FOUND.value
                    )
                }
            )

        if plugin in manager.global_plugins and channel_id:
            raise ValidationError(
                {
                    "id": ValidationError(
                        "Plugin doesn't support configuration per channel.",
                        code=PluginErrorCode.INVALID.value,
                    )
                }
            )
        elif plugin not in manager.global_plugins and not channel_id:
            raise ValidationError(
                {
                    "id": ValidationError(
                        "Plugin requires to specify channel slug.",
                        code=PluginErrorCode.NOT_FOUND.value,
                    )
                }
            )
        return {"plugin": plugin, "data": input_data, "channel_slug": channel_slug}

    @classmethod
    def perform_mutation(cls, _root, info: ResolveInfo, /, **data):
        cleaned_data = cls.clean_input(info, data)
        plugin_id = cleaned_data["plugin"].PLUGIN_ID
        channel_slug = cleaned_data["channel_slug"]
        input_data = cleaned_data["data"]
        manager = get_plugin_manager_promise(info.context).get()
        manager.save_plugin_configuration(plugin_id, channel_slug, input_data)
        manager = get_plugins_manager()
        return PluginUpdate(plugin=resolve_plugin(plugin_id, manager))
