from typing import Final

import graphene

from ...site import GiftCardSettingsExpiryType, PasswordLoginMode
from ..core.doc_category import DOC_CATEGORY_AUTH, DOC_CATEGORY_GIFT_CARDS
from ..core.enums import to_enum

GiftCardSettingsExpiryTypeEnum: Final[graphene.Enum] = to_enum(
    GiftCardSettingsExpiryType
)
GiftCardSettingsExpiryTypeEnum.doc_category = DOC_CATEGORY_GIFT_CARDS

PasswordLoginModeEnum: Final[graphene.Enum] = to_enum(
    PasswordLoginMode,
    type_name="PasswordLoginModeEnum",
    description=PasswordLoginMode.__doc__,
)
PasswordLoginModeEnum.doc_category = DOC_CATEGORY_AUTH
