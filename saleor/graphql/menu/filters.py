import django_filters
import graphene

from ...menu.models import Menu, MenuItem
from ..core.filters import ListObjectTypeFilter
from ..core.types import FilterInputObjectType
from ..utils.filters import filter_by_query_param


def filter_menu_search(qs, _, value):
    menu_fields = ["name", "slug"]
    qs = filter_by_query_param(qs, value, menu_fields)
    return qs


def filter_menu_slug(qs, _, value):
    return qs.filter(slug__in=value)


def filter_menu_item_search(qs, _, value):
    menu_item_fields = ["name"]
    qs = filter_by_query_param(qs, value, menu_item_fields)
    return qs


class MenuFilter(django_filters.FilterSet):
    search = django_filters.CharFilter(method=filter_menu_search)
    slug = ListObjectTypeFilter(input_class=graphene.String, method=filter_menu_slug)

    class Meta:
        model = Menu
        fields = ["search", "slug"]


class MenuItemFilter(django_filters.FilterSet):
    search = django_filters.CharFilter(method=filter_menu_item_search)

    class Meta:
        model = MenuItem
        fields = ["search"]


class MenuFilterInput(FilterInputObjectType):
    class Meta:
        filterset_class = MenuFilter


class MenuItemFilterInput(FilterInputObjectType):
    class Meta:
        filterset_class = MenuItemFilter
