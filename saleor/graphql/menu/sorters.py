import graphene
from django.db.models import Count, QuerySet

from ..core.types import SortInputObjectType


class MenuSortField(graphene.Enum):
    NAME = ["name", "pk"]
    ITEMS_COUNT = ["items_count", "name", "pk"]

    @property
    def description(self):
        if self.name in MenuSortField.__enum__._member_names_:
            sort_name = self.name.lower().replace("_", " ")
            return f"Sort menus by {sort_name}."
        raise ValueError("Unsupported enum value: %s" % self.value)

    @staticmethod
    def qs_with_items_count(queryset: QuerySet, **_kwargs) -> QuerySet:
        return queryset.annotate(items_count=Count("items__id"))


class MenuSortingInput(SortInputObjectType):
    class Meta:
        sort_enum = MenuSortField
        type_name = "menus"


class MenuItemsSortField(graphene.Enum):
    NAME = ["name", "sort_order"]

    @property
    def description(self):
        if self.name in MenuItemsSortField.__enum__._member_names_:
            sort_name = self.name.lower().replace("_", " ")
            return f"Sort menu items by {sort_name}."
        raise ValueError("Unsupported enum value: %s" % self.value)


class MenuItemSortingInput(SortInputObjectType):
    class Meta:
        sort_enum = MenuItemsSortField
        type_name = "menu items"
