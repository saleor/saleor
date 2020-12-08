import graphene

from ...attribute import AttributeInputType, AttributeType
from ..core.enums import to_enum

AttributeInputTypeEnum = to_enum(AttributeInputType)
AttributeTypeEnum = to_enum(AttributeType)


class AttributeValueType(graphene.Enum):
    COLOR = "COLOR"
    GRADIENT = "GRADIENT"
    URL = "URL"
    STRING = "STRING"
