import graphene

from ..core.descriptions import ADDED_IN_38
from ..core.types import SortInputObjectType


class GiftCardSortField(graphene.Enum):
    PRODUCT = ["product__name", "product__slug"]
    USED_BY = ["used_by__first_name", "used_by__last_name", "created_at"]
    CURRENT_BALANCE = ["current_balance_amount", "created_at"]
    CREATED_AT = ["created_at", "id"]

    @property
    def description(self):
        if self.name in GiftCardSortField.__enum__._member_names_:
            sort_name = self.name.lower().replace("_", " ")
            description = f"Sort gift cards by {sort_name}."
            if self.name == "CREATED_AT":
                description += ADDED_IN_38
            return description
        raise ValueError(f"Unsupported enum value: {self.value}")


class GiftCardSortingInput(SortInputObjectType):
    class Meta:
        sort_enum = GiftCardSortField
        type_name = "gift cards"
