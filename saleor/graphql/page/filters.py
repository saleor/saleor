import django_filters
import graphene
from django.db.models import Exists, FloatField, OuterRef, Q
from django.db.models.functions import Cast

from ...attribute import AttributeInputType
from ...attribute.models import AssignedPageAttributeValue, Attribute, AttributeValue
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
    ListObjectTypeWhereFilter,
    MetadataWhereBase,
    OperationObjectTypeWhereFilter,
)
from ..core.filters.where_input import (
    DecimalFilterInput,
    GlobalIDFilterInput,
    StringFilterInput,
    WhereInputObjectType,
)
from ..core.types.base import BaseInputObjectType
from ..core.types.common import DateRangeInput, DateTimeRangeInput
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


def filter_by_slug_and_name(qs, attr_id, attr_value):
    if not {"slug", "name"}.intersection(attr_value.keys()):
        return AttributeValue.objects.none()
    attribute_values = AttributeValue.objects.using(qs.db).filter(attribute_id=attr_id)
    if "slug" in attr_value:
        attribute_values = filter_where_by_value_field(
            attribute_values, "slug", attr_value["slug"]
        )
    if "name" in attr_value:
        attribute_values = filter_where_by_value_field(
            attribute_values, "name", attr_value["name"]
        )
    return attribute_values


def filter_by_numeric_attribute(qs, attr_id, attr_value):
    slug_value = attr_value.get("slug")
    name_value = attr_value.get("name")
    numeric_value = attr_value.get("numeric")
    if not any([slug_value, name_value, numeric_value]):
        return Q()

    qs_by_numeric = AttributeValue.objects.using(qs.db).filter(attribute_id=attr_id)
    if slug_value or name_value:
        qs_by_numeric = filter_by_slug_and_name(qs_by_numeric, attr_id, attr_value)

    if numeric_value:
        qs_by_numeric = qs_by_numeric.annotate(numeric_value=Cast("name", FloatField()))
        qs_by_numeric = filter_where_by_numeric_field(
            qs_by_numeric,
            "numeric_value",
            attr_value["numeric"],
        )
    assigned_attr_value = AssignedPageAttributeValue.objects.using(
        qs_by_numeric.db
    ).filter(
        Exists(qs_by_numeric.filter(id=OuterRef("value_id"))),
        page_id=OuterRef("id"),
    )
    return Q(Exists(assigned_attr_value))


def filter_by_boolean_attribute(qs, attr_id, attr_value):
    slug_value = attr_value.get("slug")
    name_value = attr_value.get("name")
    filter_over_boolean_value = "boolean" in attr_value
    if not any([slug_value, name_value, filter_over_boolean_value]):
        return Q()
    qs_by_boolean = AttributeValue.objects.using(qs.db).filter(attribute_id=attr_id)
    if slug_value or name_value:
        qs_by_boolean = filter_by_slug_and_name(qs_by_boolean, attr_id, attr_value)

    if filter_over_boolean_value:
        qs_by_boolean = qs_by_boolean.filter(boolean=attr_value["boolean"])
    assigned_attr_value = AssignedPageAttributeValue.objects.using(
        qs_by_boolean.db
    ).filter(
        Exists(qs_by_boolean.filter(id=OuterRef("value_id"))),
        page_id=OuterRef("id"),
    )
    return Q(Exists(assigned_attr_value))


def filter_by_date_attribute(qs, attr_id, attr_value):
    slug_value = attr_value.get("slug")
    name_value = attr_value.get("name")
    date_value = attr_value.get("date")
    if not any([slug_value, name_value, date_value]):
        return Q()

    qs_by_date = AttributeValue.objects.using(qs.db).filter(attribute_id=attr_id)
    if slug_value or name_value:
        qs_by_date = filter_by_slug_and_name(qs_by_date, attr_id, attr_value)

    if date_value:
        qs_by_date = filter_range_field(
            qs_by_date,
            "date_time__date",
            attr_value["date"],
        )
    assigned_attr_value = AssignedPageAttributeValue.objects.using(
        qs_by_date.db
    ).filter(
        Exists(qs_by_date.filter(id=OuterRef("value_id"))),
        page_id=OuterRef("id"),
    )
    return Q(Exists(assigned_attr_value))


def filter_by_date_time_attribute(qs, attr_id, attr_value):
    slug_value = attr_value.get("slug")
    name_value = attr_value.get("name")
    date_time_value = attr_value.get("date_time")
    if not any([slug_value, name_value, date_time_value]):
        return Q()

    qs_by_date_time = AttributeValue.objects.using(qs.db).filter(attribute_id=attr_id)
    if slug_value or name_value:
        qs_by_date_time = filter_by_slug_and_name(qs_by_date_time, attr_id, attr_value)

    if date_time_value:
        qs_by_date_time = filter_range_field(
            qs_by_date_time,
            "date_time",
            attr_value["date_time"],
        )
    assigned_attr_value = AssignedPageAttributeValue.objects.using(
        qs_by_date_time.db
    ).filter(
        Exists(qs_by_date_time.filter(id=OuterRef("value_id"))),
        page_id=OuterRef("id"),
    )
    return Exists(assigned_attr_value)


def filter_pages_by_attributes(qs, value):
    attribute_slugs = {attr_filter["slug"] for attr_filter in value}
    attributes_map = {
        attr.slug: attr
        for attr in Attribute.objects.using(qs.db).filter(slug__in=attribute_slugs)
    }
    if len(attribute_slugs) != len(attributes_map.keys()):
        # Filter over non existing attribute
        return qs.none()

    attr_filter_expression = Q()
    attr_without_values_input = [
        attributes_map[attr_filter["slug"]]
        for attr_filter in value
        if not attr_filter.get("value")
    ]
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
        attr = attributes_map[attr_filter["slug"]]
        attr_value = attr_filter["value"]
        if attr.input_type == AttributeInputType.NUMERIC:
            attr_filter_expression &= filter_by_numeric_attribute(
                qs, attr.id, attr_value
            )
        elif attr.input_type == AttributeInputType.BOOLEAN:
            attr_filter_expression &= filter_by_boolean_attribute(
                qs, attr.id, attr_value
            )
        elif attr.input_type == AttributeInputType.DATE:
            attr_filter_expression &= filter_by_date_attribute(qs, attr.id, attr_value)
        elif attr.input_type == AttributeInputType.DATE_TIME:
            attr_filter_expression &= filter_by_date_time_attribute(
                qs, attr.id, attr_value
            )
        elif "slug" in attr_value or "name" in attr_value:
            filtered_attr_values = filter_by_slug_and_name(
                AttributeValue.objects.using(qs.db).filter(attribute_id=attr.id),
                attr.id,
                attr_value,
            )
            assigned_attr_value = AssignedPageAttributeValue.objects.using(
                qs.db
            ).filter(
                Exists(filtered_attr_values.filter(id=OuterRef("value_id"))),
                page_id=OuterRef("id"),
            )
            attr_filter_expression &= Q(Exists(assigned_attr_value))
    if attr_filter_expression != Q():
        return qs.filter(attr_filter_expression)
    return qs.none()


class AttributeValuePageInput(BaseInputObjectType):
    slug = StringFilterInput(
        description="Filter by slug assigned to AttributeValue.",
    )
    name = StringFilterInput(
        description="Filter by name assigned to AttributeValue.",
    )
    numeric = DecimalFilterInput(
        required=False,
        description="Filter by numeric value for attributes of numeric type.",
    )
    date = DateRangeInput(
        required=False,
        description="Filter by date value for attributes of date type.",
    )
    date_time = DateTimeRangeInput(
        required=False,
        description="Filter by date time value for attributes of date time type.",
    )
    boolean = graphene.Boolean(
        required=False,
        description="Filter by boolean value for attributes of boolean type.",
    )


class AttributePageWhereInput(BaseInputObjectType):
    slug = graphene.String(description="Filter by attribute slug.", required=True)
    value = AttributeValuePageInput(
        required=False,
        description="Filter by values of the attribute.",
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
        input_class=AttributePageWhereInput,
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
