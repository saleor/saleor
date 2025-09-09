import graphene

from ..core.doc_category import DOC_CATEGORY_GIFT_CARDS
from ..core.types import SortInputObjectType
from ..directives import doc


@doc(category=DOC_CATEGORY_GIFT_CARDS)
class GiftCardSortField(graphene.Enum):
    PRODUCT = ["product__name", "product__slug"]
    USED_BY = ["used_by__first_name", "used_by__last_name", "created_at"]
    CURRENT_BALANCE = ["current_balance_amount", "created_at"]
    CREATED_AT = ["created_at", "id"]

    @property
    def description(self):
        if self.name in GiftCardSortField.__enum__._member_names_:
            sort_name = self.name.lower().replace("_", " ")
            return f"Sort gift cards by {sort_name}."
        raise ValueError(f"Unsupported enum value: {self.value}")


@doc(category=DOC_CATEGORY_GIFT_CARDS)
class GiftCardSortingInput(SortInputObjectType):
    class Meta:
        sort_enum = GiftCardSortField
        type_name = "gift cards"
