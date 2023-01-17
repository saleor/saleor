import django_filters
import graphene
from django.db.models import Q

from ...menu.models import Menu, MenuItem
from ..core.filters import ListObjectTypeFilter, MetadataFilterBase, filter_slug_list
from ..core.types import FilterInputObjectType


def filter_menu_search(qs, _, value):
    return qs.filter(Q(name__ilike=value) | Q(slug__ilike=value))


def filter_menu_slug(qs, _, value):
    return qs.filter(slug__in=value)


def filter_menu_item_search(qs, _, value):
    return qs.filter(name__ilike=value)


class MenuFilter(MetadataFilterBase):
    search = django_filters.CharFilter(method=filter_menu_search)
    slug = ListObjectTypeFilter(input_class=graphene.String, method=filter_menu_slug)
    slugs = ListObjectTypeFilter(input_class=graphene.String, method=filter_slug_list)

    class Meta:
        model = Menu
        fields = ["search", "slug"]


class MenuItemFilter(MetadataFilterBase):
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
