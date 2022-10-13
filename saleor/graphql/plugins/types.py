from typing import TYPE_CHECKING

import graphene

from ..channel.types import Channel
from ..core.connection import CountableConnection
from ..core.types import NonNullList
from .enums import ConfigurationTypeFieldEnum

if TYPE_CHECKING:
    from ...plugins.base_plugin import BasePlugin


class ConfigurationItem(graphene.ObjectType):
    name = graphene.String(required=True, description="Name of the field.")
    value = graphene.String(required=False, description="Current value of the field.")
    type = graphene.Field(ConfigurationTypeFieldEnum, description="Type of the field.")
    help_text = graphene.String(required=False, description="Help text for the field.")
    label = graphene.String(required=False, description="Label for the field.")

    class Meta:
        description = "Stores information about a single configuration field."


class PluginConfiguration(graphene.ObjectType):
    active = graphene.Boolean(
        required=True, description="Determines if plugin is active or not."
    )
    channel = graphene.Field(
        Channel,
        description="The channel to which the plugin configuration is assigned to.",
    )
    configuration = NonNullList(
        ConfigurationItem, description="Configuration of the plugin."
    )

    class Meta:
        description = "Stores information about a configuration of plugin."

    @staticmethod
    def resolve_configuration(root: "BasePlugin", info):
        return root.resolve_plugin_configuration(info.context)


class Plugin(graphene.ObjectType):
    id = graphene.ID(required=True, description="Identifier of the plugin.")
    name = graphene.String(description="Name of the plugin.", required=True)
    description = graphene.String(
        description="Description of the plugin.", required=True
    )
    global_configuration = graphene.Field(
        PluginConfiguration,
        description="Global configuration of the plugin (not channel-specific).",
    )
    channel_configurations = NonNullList(
        PluginConfiguration,
        description="Channel-specific plugin configuration.",
        required=True,
    )

    class Meta:
        description = "Plugin."

    @staticmethod
    def resolve_name(root: "Plugin", _info):
        return root.name

    @staticmethod
    def resolve_description(root: "Plugin", _info):
        return root.description

    @staticmethod
    def resolve_global_configuration(root: "Plugin", _info):
        return root.global_configuration

    @staticmethod
    def resolve_channel_configurations(root: "Plugin", _info):
        return root.channel_configurations or []


class PluginCountableConnection(CountableConnection):
    class Meta:
        node = Plugin
