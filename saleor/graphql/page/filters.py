from typing import Literal

import django_filters
import graphene
from django.db.models import Exists, OuterRef, Q

from ...attribute import AttributeInputType
from ...attribute.models import AssignedPageAttributeValue, Attribute, AttributeValue
from ...page import models
from ..attribute.shared_filters import (
    CONTAINS_TYPING,
    AssignedAttributeWhereInput,
    filter_by_contains_referenced_object_ids,
    filter_by_contains_referenced_pages,
    filter_by_contains_referenced_products,
    filter_by_contains_referenced_variants,
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
    filter_range_field,
    filter_slug_list,
    filter_where_by_id_field,
    filter_where_by_numeric_field,
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


def filter_by_slug_or_name(
    attr_id: int | None, attr_value: dict, db_connection_name: str
):
    attribute_values = AttributeValue.objects.using(db_connection_name).filter(
        **{"attribute_id": attr_id} if attr_id else {}
    )
    if "slug" in attr_value:
        attribute_values = filter_where_by_value_field(
            attribute_values, "slug", attr_value["slug"]
        )
    if "name" in attr_value:
        attribute_values = filter_where_by_value_field(
            attribute_values, "name", attr_value["name"]
        )
    assigned_attr_value = AssignedPageAttributeValue.objects.using(
        db_connection_name
    ).filter(
        Exists(attribute_values.filter(id=OuterRef("value_id"))),
        page_id=OuterRef("id"),
    )
    return Q(Exists(assigned_attr_value))


def filter_by_numeric_attribute(
    attr_id: int | None, numeric_value, db_connection_name: str
):
    qs_by_numeric = AttributeValue.objects.using(db_connection_name).filter(
        attribute__input_type=AttributeInputType.NUMERIC,
        **{"attribute_id": attr_id} if attr_id else {},
    )
    qs_by_numeric = filter_where_by_numeric_field(
        qs_by_numeric,
        "numeric",
        numeric_value,
    )

    assigned_attr_value = AssignedPageAttributeValue.objects.using(
        db_connection_name
    ).filter(
        value__in=qs_by_numeric,
        page_id=OuterRef("id"),
    )
    return Q(Exists(assigned_attr_value))


def filter_by_boolean_attribute(
    attr_id: int | None, boolean_value, db_connection_name: str
):
    qs_by_boolean = AttributeValue.objects.using(db_connection_name).filter(
        attribute__input_type=AttributeInputType.BOOLEAN,
        **{"attribute_id": attr_id} if attr_id else {},
    )
    qs_by_boolean = qs_by_boolean.filter(boolean=boolean_value)
    assigned_attr_value = AssignedPageAttributeValue.objects.using(
        db_connection_name
    ).filter(
        value__in=qs_by_boolean,
        page_id=OuterRef("id"),
    )
    return Q(Exists(assigned_attr_value))


def filter_by_date_attribute(attr_id: int | None, date_value, db_connection_name: str):
    qs_by_date = AttributeValue.objects.using(db_connection_name).filter(
        attribute__input_type=AttributeInputType.DATE,
        **{"attribute_id": attr_id} if attr_id else {},
    )
    qs_by_date = filter_range_field(
        qs_by_date,
        "date_time__date",
        date_value,
    )
    assigned_attr_value = AssignedPageAttributeValue.objects.using(
        db_connection_name
    ).filter(
        value__in=qs_by_date,
        page_id=OuterRef("id"),
    )
    return Q(Exists(assigned_attr_value))


def filter_by_date_time_attribute(
    attr_id: int | None, date_time_value, db_connection_name: str
):
    qs_by_date_time = AttributeValue.objects.using(db_connection_name).filter(
        attribute__input_type=AttributeInputType.DATE_TIME,
        **{"attribute_id": attr_id} if attr_id else {},
    )
    qs_by_date_time = filter_range_field(
        qs_by_date_time,
        "date_time",
        date_time_value,
    )
    assigned_attr_value = AssignedPageAttributeValue.objects.using(
        db_connection_name
    ).filter(
        value__in=qs_by_date_time,
        page_id=OuterRef("id"),
    )
    return Exists(assigned_attr_value)


def filter_pages_by_attributes(qs, value):
    attribute_slugs = {
        attr_filter["slug"] for attr_filter in value if "slug" in attr_filter
    }
    attributes_map = {
        attr.slug: attr
        for attr in Attribute.objects.using(qs.db).filter(slug__in=attribute_slugs)
    }
    if len(attribute_slugs) != len(attributes_map.keys()):
        # Filter over non existing attribute
        return qs.none()

    attr_filter_expression = Q()

    attr_without_values_input = []
    for attr_filter in value:
        if "slug" in attr_filter and "value" not in attr_filter:
            attr_without_values_input.append(attributes_map[attr_filter["slug"]])

    if attr_without_values_input:
        atr_value_qs = AttributeValue.objects.using(qs.db).filter(
            attribute_id__in=[attr.id for attr in attr_without_values_input]
        )
        assigned_attr_value = AssignedPageAttributeValue.objects.using(qs.db).filter(
            Exists(atr_value_qs.filter(id=OuterRef("value_id"))),
            page_id=OuterRef("id"),
        )
        attr_filter_expression = Q(Exists(assigned_attr_value))

    for attr_filter in value:
        attr_value = attr_filter.get("value")
        if not attr_value:
            # attrs without value input are handled separately
            continue

        attr_id = None
        if attr_slug := attr_filter.get("slug"):
            attr = attributes_map[attr_slug]
            attr_id = attr.id

        attr_value = attr_filter["value"]

        if "slug" in attr_value or "name" in attr_value:
            attr_filter_expression &= filter_by_slug_or_name(
                attr_id,
                attr_value,
                qs.db,
            )
        elif "numeric" in attr_value:
            attr_filter_expression &= filter_by_numeric_attribute(
                attr_id, attr_value["numeric"], qs.db
            )
        elif "boolean" in attr_value:
            attr_filter_expression &= filter_by_boolean_attribute(
                attr_id, attr_value["boolean"], qs.db
            )
        elif "date" in attr_value:
            attr_filter_expression &= filter_by_date_attribute(
                attr_id, attr_value["date"], qs.db
            )
        elif "date_time" in attr_value:
            attr_filter_expression &= filter_by_date_time_attribute(
                attr_id, attr_value["date_time"], qs.db
            )
        elif "reference" in attr_value:
            attr_filter_expression &= filter_pages_by_reference_attributes(
                attr_id, attr_value["reference"], qs.db
            )
    if attr_filter_expression != Q():
        return qs.filter(attr_filter_expression)
    return qs.none()


def filter_pages_by_reference_attributes(
    attr_id: int | None,
    attr_value: dict[
        Literal[
            "referenced_ids", "page_slugs", "product_slugs", "product_variant_skus"
        ],
        CONTAINS_TYPING,
    ],
    db_connection_name: str,
):
    filter_expression = Q()

    if "referenced_ids" in attr_value:
        filter_expression &= filter_by_contains_referenced_object_ids(
            attr_id,
            attr_value["referenced_ids"],
            db_connection_name,
            assigned_attr_model=AssignedPageAttributeValue,
            assigned_id_field_name="page_id",
        )
    if "page_slugs" in attr_value:
        filter_expression &= filter_by_contains_referenced_pages(
            attr_id,
            attr_value["page_slugs"],
            db_connection_name,
            assigned_attr_model=AssignedPageAttributeValue,
            assigned_id_field_name="page_id",
        )
    if "product_slugs" in attr_value:
        filter_expression &= filter_by_contains_referenced_products(
            attr_id,
            attr_value["product_slugs"],
            db_connection_name,
            assigned_attr_model=AssignedPageAttributeValue,
            assigned_id_field_name="page_id",
        )
    if "product_variant_skus" in attr_value:
        filter_expression &= filter_by_contains_referenced_variants(
            attr_id,
            attr_value["product_variant_skus"],
            db_connection_name,
            assigned_attr_model=AssignedPageAttributeValue,
            assigned_id_field_name="page_id",
        )
    return filter_expression


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
