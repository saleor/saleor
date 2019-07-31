import graphene

from ...extensions import models
from ..core.connection import CountableDjangoObjectType
from .enums import ConfigurationTypeFieldEnum


class ConfigurationItem(graphene.ObjectType):
    name = graphene.String(required=True, description="Name of the field")
    value = graphene.String(required=True, description="Current value of the field")
    type = graphene.Field(ConfigurationTypeFieldEnum, description="Type of the field")
    help_text = graphene.String(required=False, description="Help text for the field")
    label = graphene.String(required=False, description="Label for the field")


class PluginConfiguration(CountableDjangoObjectType):
    configuration = graphene.List(ConfigurationItem)

    class Meta:
        description = "Plugin configuration"
        model = models.PluginConfiguration
        interfaces = [graphene.relay.Node]
        only_fields = ["name", "description", "active", "configuration"]
