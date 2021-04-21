import graphene

from ...graphql.core.enums import to_enum
from ...plugins.base_plugin import ConfigurationTypeField

ConfigurationTypeFieldEnum = to_enum(ConfigurationTypeField)


class PluginConfigurationType(graphene.Enum):
    PER_CHANNEL = "per_channel"
    GLOBAL = "global"


#
# class UserSortField(graphene.Enum):
#     FIRST_NAME = ["first_name", "last_name", "pk"]
#     LAST_NAME = ["last_name", "first_name", "pk"]
#     EMAIL = ["email"]
#     ORDER_COUNT = ["order_count", "email"]
