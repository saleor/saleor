import graphene

from ...attribute import AttributeEntityType, AttributeInputType, AttributeType
from ..core.enums import to_enum

AttributeInputTypeEnum = to_enum(AttributeInputType)
AttributeTypeEnum = to_enum(AttributeType)
AttributeEntityTypeEnum = to_enum(AttributeEntityType)


class AttributeValueType(graphene.Enum):
    COLOR = "COLOR"
    GRADIENT = "GRADIENT"
    URL = "URL"
    STRING = "STRING"
