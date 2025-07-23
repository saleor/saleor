import django_filters
import graphene
from django.db.models import Exists, OuterRef, Q
from django.utils import timezone

from ....product.models import (
    Product,
    ProductVariant,
)
from ...core.doc_category import DOC_CATEGORY_PRODUCTS
from ...core.filters import (
    FilterInputObjectType,
    GlobalIDMultipleChoiceWhereFilter,
    ListObjectTypeFilter,
    MetadataFilterBase,
    MetadataWhereFilterBase,
    ObjectTypeFilter,
    ObjectTypeWhereFilter,
)
from ...core.filters.where_input import (
    StringFilterInput,
    WhereInputObjectType,
)
from ...core.types import (
    DateTimeRangeInput,
)
from ...utils.filters import (
    filter_by_ids,
    filter_where_by_range_field,
    filter_where_by_value_field,
)
from .shared import filter_updated_at_range


def filter_sku_list(qs, _, value):
    return qs.filter(sku__in=value)


def filter_is_preorder(qs, _, value):
    if value:
        return qs.filter(is_preorder=True).filter(
            Q(preorder_end_date__isnull=True) | Q(preorder_end_date__gte=timezone.now())
        )
    return qs.filter(
        Q(is_preorder=False)
        | (Q(is_preorder=True)) & Q(preorder_end_date__lt=timezone.now())
    )


class ProductVariantFilter(MetadataFilterBase):
    search = django_filters.CharFilter(method="product_variant_filter_search")
    sku = ListObjectTypeFilter(input_class=graphene.String, method=filter_sku_list)
    is_preorder = django_filters.BooleanFilter(method=filter_is_preorder)
    updated_at = ObjectTypeFilter(
        input_class=DateTimeRangeInput, method=filter_updated_at_range
    )

    class Meta:
        model = ProductVariant
        fields = ["search", "sku"]

    def product_variant_filter_search(self, queryset, _name, value):
        if not value:
            return queryset
        qs = Q(name__ilike=value) | Q(sku__ilike=value)
        products = (
            Product.objects.using(queryset.db).filter(name__ilike=value).values("pk")
        )
        qs |= Q(Exists(products.filter(variants=OuterRef("pk"))))
        return queryset.filter(qs)


class ProductVariantWhere(MetadataWhereFilterBase):
    ids = GlobalIDMultipleChoiceWhereFilter(method=filter_by_ids("ProductVariant"))
    sku = ObjectTypeWhereFilter(
        input_class=StringFilterInput,
        method="filter_product_sku",
        help_text="Filter by product SKU.",
    )
    updated_at = ObjectTypeWhereFilter(
        input_class=DateTimeRangeInput,
        method="filter_updated_at",
        help_text="Filter by when was the most recent update.",
    )

    class Meta:
        model = ProductVariant
        fields = []

    @staticmethod
    def filter_product_sku(qs, _, value):
        return filter_where_by_value_field(qs, "sku", value)

    @staticmethod
    def filter_updated_at(qs, _, value):
        return filter_where_by_range_field(qs, "updated_at", value)


class ProductVariantFilterInput(FilterInputObjectType):
    class Meta:
        doc_category = DOC_CATEGORY_PRODUCTS
        filterset_class = ProductVariantFilter


class ProductVariantWhereInput(WhereInputObjectType):
    class Meta:
        doc_category = DOC_CATEGORY_PRODUCTS
        filterset_class = ProductVariantWhere
