from ..core.doc_category import DOC_CATEGORY_WEBHOOKS
from ..core.types import BaseEnum, SortInputObjectType


class EventDeliverySortField(BaseEnum):
    CREATED_AT = ["created_at"]

    class Meta:
        doc_category = DOC_CATEGORY_WEBHOOKS

    @property
    def description(self):
        if self.name in EventDeliverySortField.__enum__._member_names_:
            sort_name = self.name.lower().replace("_", " ")
            return f"Sort event deliveries by {sort_name}."
        raise ValueError(f"Unsupported enum value: {self.value}")


class EventDeliverySortingInput(SortInputObjectType):
    class Meta:
        doc_category = DOC_CATEGORY_WEBHOOKS
        sort_enum = EventDeliverySortField
        type_name = "deliveries"


class EventDeliveryAttemptSortField(BaseEnum):
    CREATED_AT = ["created_at"]

    class Meta:
        doc_category = DOC_CATEGORY_WEBHOOKS

    @property
    def description(self):
        if self.name in EventDeliveryAttemptSortField.__enum__._member_names_:
            sort_name = self.name.lower().replace("_", " ")
            return f"Sort event delivery attempts by {sort_name}."
        raise ValueError(f"Unsupported enum value: {self.value}")


class EventDeliveryAttemptSortingInput(SortInputObjectType):
    class Meta:
        doc_category = DOC_CATEGORY_WEBHOOKS
        sort_enum = EventDeliveryAttemptSortField
        type_name = "attempts"
