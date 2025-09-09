from ...site import GiftCardSettingsExpiryType
from ..core.doc_category import DOC_CATEGORY_GIFT_CARDS
from ..core.enums import to_enum
from ..directives import doc

GiftCardSettingsExpiryTypeEnum = doc(
    DOC_CATEGORY_GIFT_CARDS, to_enum(GiftCardSettingsExpiryType)
)
