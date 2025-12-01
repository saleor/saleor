from typing import Final

import graphene

from ...graphql.core.enums import to_enum
from ...plugins.base_plugin import ConfigurationTypeField

ConfigurationTypeFieldEnum: Final[graphene.Enum] = to_enum(ConfigurationTypeField)


class PluginConfigurationType(graphene.Enum):
    PER_CHANNEL = "per_channel"
    GLOBAL = "global"
