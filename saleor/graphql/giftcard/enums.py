from ...giftcard import GiftCardEvents
from ..core.doc_category import DOC_CATEGORY_GIFT_CARDS
from ..core.enums import to_enum
from ..directives import doc

GiftCardEventsEnum = doc(DOC_CATEGORY_GIFT_CARDS, to_enum(GiftCardEvents))
