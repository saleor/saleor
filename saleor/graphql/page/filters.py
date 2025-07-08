import django_filters
import graphene
from django.db.models import Exists, FloatField, OuterRef, Q
from django.db.models.functions import Cast
from graphql import GraphQLError

from ...attribute import AttributeInputType
from ...attribute.models import AssignedPageAttributeValue, Attribute, AttributeValue
from ...page import models
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


def filter_by_slug_or_name(attr_id, attr_value, db_connection_name: str):
    attribute_values = AttributeValue.objects.using(db_connection_name).filter(
        attribute_id=attr_id
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


def filter_by_numeric_attribute(attr_id, numeric_value, db_connection_name: str):
    qs_by_numeric = AttributeValue.objects.using(db_connection_name).filter(
        attribute_id=attr_id
    )
    qs_by_numeric = qs_by_numeric.annotate(numeric_value=Cast("name", FloatField()))
    qs_by_numeric = filter_where_by_numeric_field(
        qs_by_numeric,
        "numeric_value",
        numeric_value,
    )
    assigned_attr_value = AssignedPageAttributeValue.objects.using(
        db_connection_name
    ).filter(
        Exists(qs_by_numeric.filter(id=OuterRef("value_id"))),
        page_id=OuterRef("id"),
    )
    return Q(Exists(assigned_attr_value))


def filter_by_boolean_attribute(attr_id, boolean_value, db_connection_name: str):
    qs_by_boolean = AttributeValue.objects.using(db_connection_name).filter(
        attribute_id=attr_id
    )
    qs_by_boolean = qs_by_boolean.filter(boolean=boolean_value)
    assigned_attr_value = AssignedPageAttributeValue.objects.using(
        db_connection_name
    ).filter(
        Exists(qs_by_boolean.filter(id=OuterRef("value_id"))),
        page_id=OuterRef("id"),
    )
    return Q(Exists(assigned_attr_value))


def filter_by_date_attribute(attr_id, date_value, db_connection_name: str):
    qs_by_date = AttributeValue.objects.using(db_connection_name).filter(
        attribute_id=attr_id
    )
    qs_by_date = filter_range_field(
        qs_by_date,
        "date_time__date",
        date_value,
    )
    assigned_attr_value = AssignedPageAttributeValue.objects.using(
        db_connection_name
    ).filter(
        Exists(qs_by_date.filter(id=OuterRef("value_id"))),
        page_id=OuterRef("id"),
    )
    return Q(Exists(assigned_attr_value))


def filter_by_date_time_attribute(attr_id, date_time_value, db_connection_name: str):
    qs_by_date_time = AttributeValue.objects.using(db_connection_name).filter(
        attribute_id=attr_id
    )
    qs_by_date_time = filter_range_field(
        qs_by_date_time,
        "date_time",
        date_time_value,
    )
    assigned_attr_value = AssignedPageAttributeValue.objects.using(
        db_connection_name
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
        if "slug" in attr_value or "name" in attr_value:
            attr_filter_expression &= filter_by_slug_or_name(
                attr.id,
                attr_value,
                qs.db,
            )
        elif attr.input_type == AttributeInputType.NUMERIC:
            attr_filter_expression &= filter_by_numeric_attribute(
                attr.id, attr_value["numeric"], qs.db
            )
        elif attr.input_type == AttributeInputType.BOOLEAN:
            attr_filter_expression &= filter_by_boolean_attribute(
                attr.id, attr_value["boolean"], qs.db
            )
        elif attr.input_type == AttributeInputType.DATE:
            attr_filter_expression &= filter_by_date_attribute(
                attr.id, attr_value["date"], qs.db
            )
        elif attr.input_type == AttributeInputType.DATE_TIME:
            attr_filter_expression &= filter_by_date_time_attribute(
                attr.id, attr_value["date_time"], qs.db
            )
    if attr_filter_expression != Q():
        return qs.filter(attr_filter_expression)
    return qs.none()


def validate_attribute_value_input(attributes: list[dict], db_connection_name: str):
    slug_list = [attr["slug"] for attr in attributes]
    value_as_empty_list = []
    value_more_than_one_list = []
    invalid_input_type_list = []
    if len(slug_list) != len(set(slug_list)):
        raise GraphQLError(
            message="Duplicated attribute slugs in attribute 'where' input are not allowed."
        )

    type_specific_value_list = {}
    for attr in attributes:
        if "value" not in attr:
            continue
        value = attr["value"]
        if not value:
            value_as_empty_list.append(attr["slug"])
            continue
        value_keys = value.keys()
        if len(value_keys) > 1:
            value_more_than_one_list.append(attr["slug"])
            continue
        value_key = list(value_keys)[0]
        if value_key not in ["slug", "name"]:
            type_specific_value_list[attr["slug"]] = value_key
        if value[value_key] is None:
            value_as_empty_list.append(attr["slug"])
            continue

    if type_specific_value_list:
        attribute_input_type_map = Attribute.objects.using(db_connection_name).in_bulk(
            type_specific_value_list.keys(),
            field_name="slug",
        )

        for attr_slug, value_key in type_specific_value_list.items():
            if attr_slug not in attribute_input_type_map:
                continue

            input_type = attribute_input_type_map[attr_slug].input_type
            if "numeric" == value_key and input_type != AttributeInputType.NUMERIC:
                invalid_input_type_list.append(attr_slug)
            if "date" == value_key and input_type != AttributeInputType.DATE:
                invalid_input_type_list.append(attr_slug)
            if "date_time" == value_key and input_type != AttributeInputType.DATE_TIME:
                invalid_input_type_list.append(attr_slug)
            if "boolean" == value_key and input_type != AttributeInputType.BOOLEAN:
                invalid_input_type_list.append(attr_slug)

    if value_as_empty_list:
        raise GraphQLError(
            message=(
                f"Incorrect input for attributes with slugs: {','.join(value_as_empty_list)}. "
                "Provided 'value' cannot be empty or null."
            )
        )
    if value_more_than_one_list:
        raise GraphQLError(
            message=(
                f"Incorrect input for attributes with slugs: {','.join(value_more_than_one_list)}. "
                "Provided 'value' must have only one input key."
            )
        )
    if invalid_input_type_list:
        raise GraphQLError(
            message=(
                f"Incorrect input for attributes with slugs: {','.join(invalid_input_type_list)}. "
                "Provided 'value' do not match the attribute input type."
            )
        )


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
        description=(
            "Filter by value of the attribute. Only one value input field is allowed. "
            "If provided more than one, the error will be raised."
        ),
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
