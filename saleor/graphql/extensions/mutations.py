import graphene

from ...extensions.manager import get_extensions_manager
from ..core.mutations import BaseMutation
from ..core.types.common import ExtensionsError
from .types import Plugin


class ExtensionsErrorMixin:
    extensions_errors = graphene.List(
        graphene.NonNull(ExtensionsError),
        description="List of errors that occurred executing the mutation.",
    )

    @classmethod
    def handle_typed_errors(cls, errors: list, **extra):
        extensions_errors = [
            ExtensionsError(field=e.field, message=e.message, code=code)
            for e, code in errors
        ]
        return cls(
            errors=[e[0] for e in errors], extensions_errors=extensions_errors, **extra
        )


class ConfigurationItemInput(graphene.InputObjectType):
    name = graphene.String(required=True, description="Name of the field to update")
    value = graphene.String(
        required=True, description="Value of the given field to update"
    )


class PluginUpdateInput(graphene.InputObjectType):
    active = graphene.Boolean(
        required=False, description="Indicates whether the plugin should be enabled"
    )
    configuration = graphene.List(
        ConfigurationItemInput,
        required=False,
        description="Configuration of the plugin",
    )


class PluginUpdate(ExtensionsErrorMixin, BaseMutation):
    plugin = graphene.Field(Plugin)

    class Arguments:
        id = graphene.ID(required=True, description="ID of plugin to update")
        input = PluginUpdateInput(
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
        instance = cls.get_node_or_error(info, plugin_id, only_type=Plugin)
        manager = get_extensions_manager()
        instance = manager.save_plugin_configuration(instance.name, input)
        return PluginUpdate(plugin=instance)
