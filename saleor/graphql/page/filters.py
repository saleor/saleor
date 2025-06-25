import django_filters
import graphene
from django.db.models import Q

from ...page import models
from ..core.doc_category import DOC_CATEGORY_PAGES
from ..core.filters import (
    FilterInputObjectType,
    GlobalIDMultipleChoiceFilter,
    ListObjectTypeFilter,
    MetadataFilterBase,
)
from ..core.filters.where_filters import (
    GlobalIDMultipleChoiceWhereFilter,
    MetadataWhereBase,
    OperationObjectTypeWhereFilter,
)
from ..core.filters.where_input import (
    GlobalIDFilterInput,
    StringFilterInput,
    WhereInputObjectType,
)
from ..utils import resolve_global_ids_to_primary_keys
from ..utils.filters import (
    filter_by_id,
    filter_by_ids,
    filter_slug_list,
    filter_where_by_id_field,
    filter_where_by_value_field,
)
from .types import Page, PageType


def search_pages(qs, value):
    if not value:
        return qs
    return qs.filter(
        Q(title__trigram_similar=value)
        | Q(slug__trigram_similar=value)
        | Q(content__icontains=value)
    )


def filter_page_page_types(qs, _, value):
    if not value:
        return qs
    _, page_types_pks = resolve_global_ids_to_primary_keys(value, PageType)
    return qs.filter(page_type_id__in=page_types_pks)


def filter_page_type_search(qs, _, value):
    if not value:
        return qs
    return qs.filter(Q(name__trigram_similar=value) | Q(slug__trigram_similar=value))


class PageWhere(MetadataWhereBase):
    ids = GlobalIDMultipleChoiceWhereFilter(method=filter_by_ids("Page"))
    slug = OperationObjectTypeWhereFilter(
        input_class=StringFilterInput,
        method="filter_page_slug",
        help_text="Filter by page slug.",
    )
    page_type = OperationObjectTypeWhereFilter(
        input_class=GlobalIDFilterInput,
        method="filter_page_type",
        help_text="Filter by page type.",
    )

    @staticmethod
    def filter_page_slug(qs, _, value):
        return filter_where_by_value_field(qs, "slug", value)

    @staticmethod
    def filter_page_type(qs, _, value):
        if not value:
            return qs
        return filter_where_by_id_field(qs, "page_type", value, "PageType")


def filter_page_search(qs, _, value):
    # Skip search, as search is applied on resolver side.
    return qs


class PageFilter(MetadataFilterBase):
    search = django_filters.CharFilter(method=filter_page_search)
    page_types = GlobalIDMultipleChoiceFilter(method=filter_page_page_types)
    ids = GlobalIDMultipleChoiceFilter(method=filter_by_id(Page))
    slugs = ListObjectTypeFilter(input_class=graphene.String, method=filter_slug_list)

    class Meta:
        model = models.Page
        fields = ["search"]


class PageFilterInput(FilterInputObjectType):
    class Meta:
        doc_category = DOC_CATEGORY_PAGES
        filterset_class = PageFilter


class PageWhereInput(WhereInputObjectType):
    class Meta:
        doc_category = DOC_CATEGORY_PAGES
        filterset_class = PageWhere


class PageTypeFilter(django_filters.FilterSet):
    search = django_filters.CharFilter(method=filter_page_type_search)
    slugs = ListObjectTypeFilter(input_class=graphene.String, method=filter_slug_list)


class PageTypeFilterInput(FilterInputObjectType):
    class Meta:
        doc_category = DOC_CATEGORY_PAGES
        filterset_class = PageTypeFilter
