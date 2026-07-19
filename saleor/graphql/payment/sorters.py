from ..core.descriptions import ADDED_IN_323
from ..core.doc_category import DOC_CATEGORY_PAYMENTS
from ..core.types import BaseEnum, SortInputObjectType


class TransactionSortField(BaseEnum):
    CREATED_AT = ["created_at", "pk"]
    MODIFIED_AT = ["modified_at", "pk"]

    class Meta:
        doc_category = DOC_CATEGORY_PAYMENTS

    @property
    def description(self):
        descriptions = {
            TransactionSortField.CREATED_AT.name: "creation date.",  # type: ignore[attr-defined] # graphene.Enum is not typed # noqa: E501
            TransactionSortField.MODIFIED_AT.name: "modification date.",  # type: ignore[attr-defined] # graphene.Enum is not typed # noqa: E501
        }
        if self.name in descriptions:
            return f"Sort transactions by {descriptions[self.name]} {ADDED_IN_323}"
        raise ValueError(f"Unsupported enum value: {self.value}")


class TransactionSortingInput(SortInputObjectType):
    class Meta:
        doc_category = DOC_CATEGORY_PAYMENTS
        sort_enum = TransactionSortField
        type_name = "transactions"
