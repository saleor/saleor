from enum import Enum

import graphene

from ...attribute import AttributeEntityType, AttributeInputType, AttributeType
from ..core.doc_category import DOC_CATEGORY_ATTRIBUTES
from ..core.enums import to_enum
from ..core.utils import str_to_enum

AttributeInputTypeEnum = to_enum(AttributeInputType)
AttributeInputTypeEnum.doc_category = DOC_CATEGORY_ATTRIBUTES

AttributeTypeEnum = to_enum(AttributeType)
AttributeTypeEnum.doc_category = DOC_CATEGORY_ATTRIBUTES

AttributeEntityTypeEnum = to_enum(AttributeEntityType)
AttributeEntityTypeEnum.doc_category = DOC_CATEGORY_ATTRIBUTES

AttributeEntityTypeEnum = graphene.Enum(
    "AttributeEntityTypeEnum",
    [(str_to_enum(name.upper()), code) for code, name in AttributeEntityType.CHOICES],
)
AttributeEntityTypeEnum.doc_category = DOC_CATEGORY_ATTRIBUTES


class AttributeValueBulkActionEnum(Enum):
    NONE = None
    CREATE = "create"
    GET_OR_CREATE = "get_or_create"
    UPDATE_OR_CREATE = "update_or_create"
