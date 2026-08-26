from typing import Final

import graphene

from ...product import MediaOwnerTypes, ProductMediaTypes
from ..core.doc_category import DOC_CATEGORY_MEDIA
from ..core.enums import to_enum

MediaType: Final[graphene.Enum] = to_enum(ProductMediaTypes, type_name="MediaType")
MediaType.doc_category = DOC_CATEGORY_MEDIA

MediaOwnerType: Final[graphene.Enum] = to_enum(
    MediaOwnerTypes, type_name="MediaOwnerType"
)
MediaOwnerType.doc_category = DOC_CATEGORY_MEDIA
