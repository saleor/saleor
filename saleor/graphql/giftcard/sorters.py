import graphene

from ..core.types import SortInputObjectType


class GiftCardSortField(graphene.Enum):
    PRODUCT = ["product__name", "product__slug"]
    USED_BY = ["used_by__first_name", "used_by__last_name", "created_at"]
    CURRENT_BALANCE = ["current_balance_amount", "created_at"]

    @property
    def description(self):
        if self.name in GiftCardSortField.__enum__._member_names_:
            sort_name = self.name.lower().replace("_", " ")
            return f"Sort orders by {sort_name}."
        raise ValueError("Unsupported enum value: %s" % self.value)


class GiftCardSortingInput(SortInputObjectType):
    class Meta:
        sort_enum = GiftCardSortField
        type_name = "gift cards"
