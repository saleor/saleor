from ...giftcard import GiftCardEvents
from ..core.doc_category import DOC_CATEGORY_GIFT_CARDS
from ..core.enums import to_enum

GiftCardEventsEnum = to_enum(GiftCardEvents)
GiftCardEventsEnum.doc_category = DOC_CATEGORY_GIFT_CARDS
