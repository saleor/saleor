from enum import Enum

import graphene

from ...attribute import AttributeEntityType, AttributeInputType, AttributeType
from ..core.doc_category import DOC_CATEGORY_ATTRIBUTES
from ..core.enums import to_enum
from ..core.utils import str_to_enum
from ..directives import doc

AttributeInputTypeEnum = doc(DOC_CATEGORY_ATTRIBUTES, to_enum(AttributeInputType))

AttributeTypeEnum = doc(DOC_CATEGORY_ATTRIBUTES, to_enum(AttributeType))

AttributeEntityTypeEnum = doc(DOC_CATEGORY_ATTRIBUTES, to_enum(AttributeEntityType))

AttributeEntityTypeEnum = doc(
    DOC_CATEGORY_ATTRIBUTES,
    graphene.Enum(
        "AttributeEntityTypeEnum",
        [
            (str_to_enum(name.upper()), code)
            for code, name in AttributeEntityType.CHOICES
        ],
    ),
)


class AttributeValueBulkActionEnum(Enum):
    NONE = None
    CREATE = "create"
    GET_OR_CREATE = "get_or_create"
    UPDATE_OR_CREATE = "update_or_create"
