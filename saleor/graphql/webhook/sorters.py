import graphene

from ..core.doc_category import DOC_CATEGORY_WEBHOOKS
from ..core.types import SortInputObjectType
from ..directives import doc


@doc(category=DOC_CATEGORY_WEBHOOKS)
class EventDeliverySortField(graphene.Enum):
    CREATED_AT = ["created_at"]

    @property
    def description(self):
        if self.name in EventDeliverySortField.__enum__._member_names_:
            sort_name = self.name.lower().replace("_", " ")
            return f"Sort event deliveries by {sort_name}."
        raise ValueError(f"Unsupported enum value: {self.value}")


@doc(category=DOC_CATEGORY_WEBHOOKS)
class EventDeliverySortingInput(SortInputObjectType):
    class Meta:
        sort_enum = EventDeliverySortField
        type_name = "deliveries"


@doc(category=DOC_CATEGORY_WEBHOOKS)
class EventDeliveryAttemptSortField(graphene.Enum):
    CREATED_AT = ["created_at"]

    @property
    def description(self):
        if self.name in EventDeliveryAttemptSortField.__enum__._member_names_:
            sort_name = self.name.lower().replace("_", " ")
            return f"Sort event delivery attempts by {sort_name}."
        raise ValueError(f"Unsupported enum value: {self.value}")


@doc(category=DOC_CATEGORY_WEBHOOKS)
class EventDeliveryAttemptSortingInput(SortInputObjectType):
    class Meta:
        sort_enum = EventDeliveryAttemptSortField
        type_name = "attempts"
