import django_filters
import graphene
from django.db.models import Exists, OuterRef, Q
from django.db.models.query import QuerySet
from django.utils import timezone

from ....attribute.models import (
    AssignedVariantAttribute,
    AssignedVariantAttributeValue,
    AttributeValue,
)
from ....product.models import Product, ProductVariant
from ...attribute.shared_filters import (
    AssignedAttributeWhereInput,
    filter_objects_by_attributes,
    validate_attribute_value_input,
)
from ...core.descriptions import ADDED_IN_322
from ...core.doc_category import DOC_CATEGORY_PRODUCTS
from ...core.filters import (
    FilterInputObjectType,
    GlobalIDMultipleChoiceWhereFilter,
    ListObjectTypeFilter,
    ListObjectTypeWhereFilter,
    MetadataFilterBase,
    MetadataWhereFilterBase,
    ObjectTypeFilter,
    ObjectTypeWhereFilter,
)
from ...core.filters.where_input import StringFilterInput, WhereInputObjectType
from ...core.types import DateTimeRangeInput
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


def _get_assigned_variant_attribute_for_attribute_value_qs(
    attribute_values: QuerySet[AttributeValue],
    db_connection_name: str,
):
    assigned_attr_value = AssignedVariantAttributeValue.objects.using(
        db_connection_name
    ).filter(
        value__in=attribute_values,
        assignment_id=OuterRef("id"),
    )
    return Q(
        Exists(
            AssignedVariantAttribute.objects.using(db_connection_name).filter(
                Exists(assigned_attr_value), variant_id=OuterRef("pk")
            )
        )
    )


def filter_variants_by_attributes(
    qs: QuerySet[ProductVariant], value: list[dict]
) -> QuerySet[ProductVariant]:
    return filter_objects_by_attributes(
        qs,
        value,
        _get_assigned_variant_attribute_for_attribute_value_qs,
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
    attributes = ListObjectTypeWhereFilter(
        input_class=AssignedAttributeWhereInput,
        method="filter_attributes",
        help_text="Filter by attributes associated with the variant." + ADDED_IN_322,
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

    @staticmethod
    def filter_attributes(qs, _, value):
        if not value:
            return qs
        return filter_variants_by_attributes(qs, value)

    def is_valid(self):
        if attributes := self.data.get("attributes"):
            validate_attribute_value_input(attributes, self.queryset.db)
        return super().is_valid()


class ProductVariantFilterInput(FilterInputObjectType):
    class Meta:
        doc_category = DOC_CATEGORY_PRODUCTS
        filterset_class = ProductVariantFilter


class ProductVariantWhereInput(WhereInputObjectType):
    class Meta:
        doc_category = DOC_CATEGORY_PRODUCTS
        filterset_class = ProductVariantWhere
