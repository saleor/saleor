import django_filters
import graphene
from django.db.models import Q

from ...attribute.models import AssignedPageAttributeValue
from ...page import models
from ..attribute.shared_filters import (
    AssignedAttributeWhereInput,
    filter_objects_by_attributes,
    validate_attribute_value_input,
)
from ..core.context import ChannelQsContext
from ..core.doc_category import DOC_CATEGORY_PAGES
from ..core.filters import (
    FilterInputObjectType,
    GlobalIDMultipleChoiceFilter,
    ListObjectTypeFilter,
    MetadataFilterBase,
)
from ..core.filters.where_filters import (
    GlobalIDMultipleChoiceWhereFilter,
    ListObjectTypeWhereFilter,
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


def search_pages(channel_qs: ChannelQsContext, value):
    if not value:
        return channel_qs
    channel_qs.qs = channel_qs.qs.filter(
        Q(title__trigram_similar=value)
        | Q(slug__trigram_similar=value)
        | Q(content__icontains=value)
    )
    return channel_qs


def filter_page_page_types(qs, _, value):
    if not value:
        return qs
    _, page_types_pks = resolve_global_ids_to_primary_keys(value, PageType)
    return qs.filter(page_type_id__in=page_types_pks)


def filter_page_type_search(qs, _, value):
    if not value:
        return qs
    return qs.filter(Q(name__trigram_similar=value) | Q(slug__trigram_similar=value))


def filter_pages_by_attributes(qs, value):
    return filter_objects_by_attributes(
        qs,
        value,
        AssignedPageAttributeValue,
        "page_id",
    )


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
    attributes = ListObjectTypeWhereFilter(
        input_class=AssignedAttributeWhereInput,
        method="filter_attributes",
        help_text="Filter by attributes associated with the page.",
    )

    @staticmethod
    def filter_page_slug(qs, _, value):
        return filter_where_by_value_field(qs, "slug", value)

    @staticmethod
    def filter_page_type(qs, _, value):
        if not value:
            return qs
        return filter_where_by_id_field(qs, "page_type", value, "PageType")

    @staticmethod
    def filter_attributes(qs, _, value):
        if not value:
            return qs
        return filter_pages_by_attributes(qs, value)

    def is_valid(self):
        if attributes := self.data.get("attributes"):
            validate_attribute_value_input(attributes, self.queryset.db)
        return super().is_valid()


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
