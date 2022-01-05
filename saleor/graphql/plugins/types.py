from typing import TYPE_CHECKING, List

import graphene

from ..channel.types import Channel
from ..core.connection import CountableConnection
from .dataloaders import EmailTemplatesByPluginConfigurationLoader
from .enums import ConfigurationTypeFieldEnum

if TYPE_CHECKING:
    from ...plugins import models
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
    configuration = graphene.List(
        ConfigurationItem, description="Configuration of the plugin."
    )

    class Meta:
        description = "Stores information about a configuration of plugin."

    @staticmethod
    def resolve_configuration(root: "BasePlugin", info, **_kwargs):
        # Here we are getting email templates from the database and merging them with
        # root.configuration. Consider if we should do it here or inside of the "getter"
        # of root.configuration field. With the current approach we manually call the DB
        # here which gives us control over DB queries; see if we would have the same
        # control when DB call is moved deeper to the getter.

        def map_templates_to_configuration(
            email_templates: List["models.EmailTemplate"],
        ):
            for email_template in email_templates:
                for index, config_item in enumerate(root.configuration):
                    if config_item["name"] == email_template.name:
                        root.configuration[index]["value"] = email_template.value
            return root.configuration

        if root.db_config:
            return (
                EmailTemplatesByPluginConfigurationLoader(info.context)
                .load(root.db_config.pk)
                .then(map_templates_to_configuration)
            )
        else:
            return root.configuration


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
    channel_configurations = graphene.List(
        graphene.NonNull(PluginConfiguration),
        description="Channel-specific plugin configuration.",
        required=True,
    )

    class Meta:
        description = "Plugin."

    @staticmethod
    def resolve_id(root: "Plugin", _info):
        return root.id

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
