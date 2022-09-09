import graphene

from ...attribute import AttributeEntityType, AttributeInputType, AttributeType
from ..core.enums import to_enum
from ..core.utils import str_to_enum

AttributeInputTypeEnum = to_enum(AttributeInputType)
AttributeTypeEnum = to_enum(AttributeType)
AttributeEntityTypeEnum = to_enum(AttributeEntityType)

AttributeEntityTypeEnum = graphene.Enum(
    "AttributeEntityTypeEnum",
    [(str_to_enum(name.upper()), code) for code, name in AttributeEntityType.CHOICES],
)
