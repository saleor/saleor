import django_filters
import graphene
from django.db.models import Q

from ....product.models import Category
from ...core.doc_category import DOC_CATEGORY_PRODUCTS
from ...core.filters import (
    FilterInputObjectType,
    GlobalIDMultipleChoiceFilter,
    GlobalIDMultipleChoiceWhereFilter,
    ListObjectTypeFilter,
    MetadataFilterBase,
    MetadataWhereFilterBase,
    ObjectTypeFilter,
)
from ...core.filters.where_input import (
    WhereInputObjectType,
)
from ...core.types import (
    DateTimeRangeInput,
)
from ...utils.filters import (
    filter_by_ids,
    filter_slug_list,
)
from .shared import filter_updated_at_range


class CategoryFilter(MetadataFilterBase):
    search = django_filters.CharFilter(method="category_filter_search")
    ids = GlobalIDMultipleChoiceFilter(field_name="id")
    slugs = ListObjectTypeFilter(input_class=graphene.String, method=filter_slug_list)
    updated_at = ObjectTypeFilter(
        input_class=DateTimeRangeInput,
        method=filter_updated_at_range,
        help_text="Filter by when was the most recent update.",
    )

    class Meta:
        model = Category
        fields = ["search"]

    @classmethod
    def category_filter_search(cls, queryset, _name, value):
        if not value:
            return queryset
        name_slug_desc_qs = (
            Q(name__ilike=value)
            | Q(slug__ilike=value)
            | Q(description_plaintext__ilike=value)
        )

        return queryset.filter(name_slug_desc_qs)


class CategoryWhere(MetadataWhereFilterBase):
    ids = GlobalIDMultipleChoiceWhereFilter(method=filter_by_ids("Category"))
    # Category where filter is also used in promotion logic. In case of extending it
    # the category update mutation should also be modified to recalculate the prices
    # for new added field.

    class Meta:
        model = Category
        fields = []


class CategoryFilterInput(FilterInputObjectType):
    class Meta:
        doc_category = DOC_CATEGORY_PRODUCTS
        filterset_class = CategoryFilter


class CategoryWhereInput(WhereInputObjectType):
    class Meta:
        doc_category = DOC_CATEGORY_PRODUCTS
        filterset_class = CategoryWhere
