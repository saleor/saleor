import graphene

from ...extensions import ConfigurationTypeField, manager, models
from ..core.connection import CountableDjangoObjectType
from .enums import ConfigurationTypeFieldEnum


def hide_private_configuration_fields(configuration, config_structure):
    for field in configuration:
        name = field["name"]
        value = field["value"]
        if value is None:
            continue
        field_type = config_structure.get(name, {}).get("type")
        if field_type == ConfigurationTypeField.PASSWORD:
            field["value"] = "" if value else None

        if field_type == ConfigurationTypeField.SECRET:
            if not value:
                field["value"] = None
            elif len(value) > 4:
                field["value"] = value[-4:]
            else:
                field["value"] = value[-1:]


class ConfigurationItem(graphene.ObjectType):
    name = graphene.String(required=True, description="Name of the field.")
    value = graphene.String(required=False, description="Current value of the field.")
    type = graphene.Field(ConfigurationTypeFieldEnum, description="Type of the field.")
    help_text = graphene.String(required=False, description="Help text for the field.")
    label = graphene.String(required=False, description="Label for the field.")

    class Meta:
        description = "Stores information about a single configuration field."


class Plugin(CountableDjangoObjectType):
    configuration = graphene.List(ConfigurationItem)

    class Meta:
        description = "Plugin."
        model = models.PluginConfiguration
        interfaces = [graphene.relay.Node]
        only_fields = ["name", "description", "active", "configuration"]

    @staticmethod
    def resolve_configuration(root: models.PluginConfiguration, _info):
        plugin = manager.get_extensions_manager().get_plugin(root.name)
        configuration = plugin.get_plugin_configuration().configuration
        if plugin.CONFIG_STRUCTURE and configuration:
            hide_private_configuration_fields(configuration, plugin.CONFIG_STRUCTURE)
        return configuration
