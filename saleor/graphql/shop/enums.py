from ...site import GiftCardSettingsExpiryType
from ..core.doc_category import DOC_CATEGORY_GIFT_CARDS
from ..core.enums import to_enum

GiftCardSettingsExpiryTypeEnum = to_enum(GiftCardSettingsExpiryType)
GiftCardSettingsExpiryTypeEnum.doc_category = DOC_CATEGORY_GIFT_CARDS
