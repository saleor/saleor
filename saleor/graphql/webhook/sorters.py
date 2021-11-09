import graphene

from ..core.types import SortInputObjectType


class EventDeliverySortField(graphene.Enum):
    CREATED_AT = ["created_at"]

    @property
    def description(self):
        if self.name in EventDeliverySortField.__enum__._member_names_:
            sort_name = self.name.lower().replace("_", " ")
            return f"Sort pages by {sort_name}."
        raise ValueError("Unsupported enum value: %s" % self.value)


class EventDeliverySortingInput(SortInputObjectType):
    class Meta:
        sort_enum = EventDeliverySortField
        type_name = "deliveries"
