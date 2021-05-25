import django_filters
from graphene_django.filter import GlobalIDMultipleChoiceFilter

from ...page import models
from ..core.filters import MetadataFilterBase
from ..core.types import FilterInputObjectType
from ..utils import resolve_global_ids_to_primary_keys
from ..utils.filters import filter_by_query_param
from .types import Page


def filter_page_search(qs, _, value):
    page_fields = ["content", "slug", "title"]
    qs = filter_by_query_param(qs, value, page_fields)
    return qs


def filter_page_ids(qs, _, value):
    if not value:
        return qs
    _, page_pks = resolve_global_ids_to_primary_keys(value, Page)
    return qs.filter(id__in=page_pks)


def filter_page_type_search(qs, _, value):
    fields = ["name", "slug"]
    if value:
        qs = filter_by_query_param(qs, value, fields)
    return qs


class PageFilter(MetadataFilterBase):
    search = django_filters.CharFilter(method=filter_page_search)
    page_types = GlobalIDMultipleChoiceFilter(field_name="page_type")
    ids = GlobalIDMultipleChoiceFilter(method=filter_page_ids)

    class Meta:
        model = models.Page
        fields = ["search"]


class PageFilterInput(FilterInputObjectType):
    class Meta:
        filterset_class = PageFilter


class PageTypeFilter(django_filters.FilterSet):
    search = django_filters.CharFilter(method=filter_page_type_search)


class PageTypeFilterInput(FilterInputObjectType):
    class Meta:
        filterset_class = PageTypeFilter
