from typing import Final

import graphene

from ...product import MediaOwnerTypes, ProductMediaTypes
from ..core.descriptions import ADDED_IN_324
from ..core.doc_category import DOC_CATEGORY_MEDIA
from ..core.enums import to_enum

MediaType: Final[graphene.Enum] = to_enum(
    ProductMediaTypes,
    type_name="MediaType",
    description="The kind of content a media item holds." + ADDED_IN_324,
)
MediaType.doc_category = DOC_CATEGORY_MEDIA

MediaOwnerType: Final[graphene.Enum] = to_enum(
    MediaOwnerTypes,
    type_name="MediaOwnerType",
    description="The kind of entity a media item belongs to." + ADDED_IN_324,
)
MediaOwnerType.doc_category = DOC_CATEGORY_MEDIA
