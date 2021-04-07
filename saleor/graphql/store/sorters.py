import graphene
from django.db.models import Count, QuerySet
from ..core.types import SortInputObjectType


class StoreSortField(graphene.Enum):
    NAME = ["name", "pk"]
    DESCRIPTION = ["description", "pk"]
    
    @property
    def description(self):
        if self.name in StoreSortField.__enum__._member_names_:
            sort_name = self.name.lower().replace("_", " ")
            return f"Sort users by {sort_name}."
        raise ValueError("Unsupported enum value: %s" % self.value)

    @staticmethod
    def qs_with_order_count(queryset: QuerySet, **_kwargs) -> QuerySet:
        return queryset.annotate(order_count=Count("orders__id"))


class StoreSortingInput(SortInputObjectType):
    class Meta:
        sort_enum = StoreSortField
        type_name = "stores"
