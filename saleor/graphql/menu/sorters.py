import graphene
from django.db.models import Count, QuerySet

from ..core.types import SortInputObjectType


class MenuSortField(graphene.Enum):
    NAME = ["name", "pk"]
    ITEMS_COUNT = ["items_count", "name", "pk"]

    @property
    def description(self):
        # pylint: disable=no-member
        if self in [MenuSortField.NAME, MenuSortField.ITEMS_COUNT]:
            sort_name = self.name.lower().replace("_", " ")
            return f"Sort menus by {sort_name}."
        raise ValueError("Unsupported enum value: %s" % self.value)

    @staticmethod
    def qs_with_items_count(queryset: QuerySet) -> QuerySet:
        return queryset.annotate(items_count=Count("items__id"))


class MenuSortingInput(SortInputObjectType):
    class Meta:
        sort_enum = MenuSortField
        type_name = "menus"


class MenuItemsSortField(graphene.Enum):
    NAME = ["name", "sort_order"]

    @property
    def description(self):
        # pylint: disable=no-member
        if self in [MenuItemsSortField.NAME]:
            sort_name = self.name.lower().replace("_", " ")
            return f"Sort menu items by {sort_name}."
        raise ValueError("Unsupported enum value: %s" % self.value)


class MenuItemSortingInput(SortInputObjectType):
    class Meta:
        sort_enum = MenuItemsSortField
        type_name = "menu items"
