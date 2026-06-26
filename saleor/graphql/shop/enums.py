from typing import Final

import graphene

from ...site import AnnouncementImportance, GiftCardSettingsExpiryType
from ..core.doc_category import DOC_CATEGORY_GIFT_CARDS, DOC_CATEGORY_SHOP
from ..core.enums import to_enum

GiftCardSettingsExpiryTypeEnum: Final[graphene.Enum] = to_enum(
    GiftCardSettingsExpiryType
)
GiftCardSettingsExpiryTypeEnum.doc_category = DOC_CATEGORY_GIFT_CARDS

AnnouncementImportanceEnum: Final[graphene.Enum] = to_enum(
    AnnouncementImportance,
    type_name="AnnouncementImportanceEnum",
    description=AnnouncementImportance.__doc__,
)
AnnouncementImportanceEnum.doc_category = DOC_CATEGORY_SHOP
