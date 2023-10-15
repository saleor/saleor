import django_filters
import graphene
from django.db.models import Q

from ...attribute import AttributeInputType
from ...attribute.models import Attribute, AttributeValue
from ...permission.utils import has_one_of_permissions
from ...product import models
from ...product.models import ALL_PRODUCTS_PERMISSIONS
from ..channel.filters import get_channel_slug_from_filter_data
from ..core.descriptions import ADDED_IN_311, PREVIEW_FEATURE
from ..core.doc_category import DOC_CATEGORY_ATTRIBUTES
from ..core.enums import MeasurementUnitsEnum
from ..core.filters import (
    BooleanWhereFilter,
    EnumFilter,
    GlobalIDFilter,
    GlobalIDMultipleChoiceFilter,
    GlobalIDMultipleChoiceWhereFilter,
    GlobalIDWhereFilter,
    ListObjectTypeFilter,
    MetadataFilterBase,
    MetadataWhereFilterBase,
    OperationObjectTypeWhereFilter,
    filter_slug_list,
)
from ..core.types import (
    BaseInputObjectType,
    ChannelFilterInputObjectType,
    FilterInputObjectType,
    NonNullList,
    StringFilterInput,
)
from ..core.types.filter_input import FilterInputDescriptions, WhereInputObjectType
from ..core.utils import from_global_id_or_error
from ..utils import get_user_or_app_from_context
from ..utils.filters import filter_by_ids, filter_where_by_string_field
from .enums import AttributeEntityTypeEnum, AttributeInputTypeEnum, AttributeTypeEnum


def filter_attributes_by_product_types(qs, field, value, requestor, channel_slug):
    if not value:
        return qs

    product_qs = models.Product.objects.visible_to_user(requestor, channel_slug)

    if field == "in_category":
        _type, category_id = from_global_id_or_error(value, "Category")
        category = models.Category.objects.filter(pk=category_id).first()

        if category is None:
            return qs.none()

        tree = category.get_descendants(include_self=True)
        product_qs = product_qs.filter(category__in=tree)

        if not has_one_of_permissions(requestor, ALL_PRODUCTS_PERMISSIONS):
            product_qs = product_qs.annotate_visible_in_listings(channel_slug).exclude(
                visible_in_listings=False
            )

    elif field == "in_collection":
        _type, collection_id = from_global_id_or_error(value, "Collection")
        product_qs = product_qs.filter(collections__id=collection_id)

    else:
        raise NotImplementedError(f"Filtering by {field} is unsupported")

    product_types = set(product_qs.values_list("product_type_id", flat=True))
    return qs.filter(
        Q(product_types__in=product_types) | Q(product_variant_types__in=product_types)
    )


def filter_attribute_search(qs, _, value):
    if not value:
        return qs
    return qs.filter(Q(slug__ilike=value) | Q(name__ilike=value))


def filter_by_attribute_type(qs, _, value):
    if not value:
        return qs
    return qs.filter(type=value)


class AttributeValueFilter(django_filters.FilterSet):
    search = django_filters.CharFilter(method="filter_search")
    ids = GlobalIDMultipleChoiceFilter(field_name="id")
    slugs = ListObjectTypeFilter(input_class=graphene.String, method=filter_slug_list)

    class Meta:
        model = AttributeValue
        fields = ["search"]

    @classmethod
    def filter_search(cls, queryset, _name, value):
        if not value:
            return queryset
        name_slug_qs = Q(name__ilike=value) | Q(slug__ilike=value)

        return queryset.filter(name_slug_qs)


class AttributeFilter(MetadataFilterBase):
    search = django_filters.CharFilter(method=filter_attribute_search)
    ids = GlobalIDMultipleChoiceFilter(field_name="id")
    type = EnumFilter(input_class=AttributeTypeEnum, method=filter_by_attribute_type)

    in_collection = GlobalIDFilter(method="filter_in_collection")
    in_category = GlobalIDFilter(method="filter_in_category")
    slugs = ListObjectTypeFilter(input_class=graphene.String, method=filter_slug_list)

    class Meta:
        model = Attribute
        fields = [
            "value_required",
            "is_variant_only",
            "visible_in_storefront",
            "filterable_in_storefront",
            "filterable_in_dashboard",
            "available_in_grid",
        ]

    def filter_in_collection(self, qs, name, value):
        requestor = get_user_or_app_from_context(self.request)
        channel_slug = get_channel_slug_from_filter_data(self.data)
        return filter_attributes_by_product_types(
            qs, name, value, requestor, channel_slug
        )

    def filter_in_category(self, qs, name, value):
        requestor = get_user_or_app_from_context(self.request)
        channel_slug = get_channel_slug_from_filter_data(self.data)
        return filter_attributes_by_product_types(
            qs, name, value, requestor, channel_slug
        )


class AttributeFilterInput(ChannelFilterInputObjectType):
    class Meta:
        doc_category = DOC_CATEGORY_ATTRIBUTES
        filterset_class = AttributeFilter


class AttributeValueFilterInput(FilterInputObjectType):
    class Meta:
        doc_category = DOC_CATEGORY_ATTRIBUTES
        filterset_class = AttributeValueFilter


class AttributeInputTypeEnumFilterInput(BaseInputObjectType):
    eq = AttributeInputTypeEnum(description=FilterInputDescriptions.EQ, required=False)
    one_of = NonNullList(
        AttributeInputTypeEnum,
        description=FilterInputDescriptions.ONE_OF,
        required=False,
    )

    class Meta:
        doc_category = DOC_CATEGORY_ATTRIBUTES


class AttributeEntityTypeEnumFilterInput(BaseInputObjectType):
    eq = AttributeEntityTypeEnum(description=FilterInputDescriptions.EQ, required=False)
    one_of = NonNullList(
        AttributeEntityTypeEnum,
        description=FilterInputDescriptions.ONE_OF,
        required=False,
    )

    class Meta:
        doc_category = DOC_CATEGORY_ATTRIBUTES


class AttributeTypeEnumFilterInput(BaseInputObjectType):
    eq = AttributeTypeEnum(description=FilterInputDescriptions.EQ, required=False)
    one_of = NonNullList(
        AttributeTypeEnum,
        description=FilterInputDescriptions.ONE_OF,
        required=False,
    )

    class Meta:
        doc_category = DOC_CATEGORY_ATTRIBUTES


class MeasurementUnitsEnumFilterInput(BaseInputObjectType):
    eq = MeasurementUnitsEnum(description=FilterInputDescriptions.EQ, required=False)
    one_of = NonNullList(
        MeasurementUnitsEnum,
        description=FilterInputDescriptions.ONE_OF,
        required=False,
    )

    class Meta:
        doc_category = DOC_CATEGORY_ATTRIBUTES


def filter_attribute_name(qs, _, value):
    return filter_where_by_string_field(qs, "name", value)


def filter_attribute_slug(qs, _, value):
    return filter_where_by_string_field(qs, "slug", value)


def filter_with_choices(qs, _, value):
    lookup = Q(input_type__in=AttributeInputType.TYPES_WITH_CHOICES)
    if value is True:
        return qs.filter(lookup)
    elif value is False:
        return qs.exclude(lookup)
    return qs.none()


def filter_attribute_input_type(qs, _, value):
    return filter_where_by_string_field(qs, "input_type", value)


def filter_attribute_entity_type(qs, _, value):
    return filter_where_by_string_field(qs, "entity_type", value)


def filter_attribute_type(qs, _, value):
    return filter_where_by_string_field(qs, "type", value)


def filter_attribute_unit(qs, _, value):
    return filter_where_by_string_field(qs, "unit", value)


def where_filter_attributes_by_product_types(qs, field, value, requestor, channel_slug):
    if not value:
        return qs.none()

    return filter_attributes_by_product_types(qs, field, value, requestor, channel_slug)


class AttributeWhere(MetadataWhereFilterBase):
    ids = GlobalIDMultipleChoiceWhereFilter(method=filter_by_ids("Attribute"))
    name = OperationObjectTypeWhereFilter(
        input_class=StringFilterInput, method=filter_attribute_name
    )
    slug = OperationObjectTypeWhereFilter(
        input_class=StringFilterInput, method=filter_attribute_slug
    )
    with_choices = BooleanWhereFilter(method=filter_with_choices)
    input_type = OperationObjectTypeWhereFilter(
        AttributeInputTypeEnumFilterInput, method=filter_attribute_input_type
    )
    entity_type = OperationObjectTypeWhereFilter(
        AttributeEntityTypeEnumFilterInput, method=filter_attribute_entity_type
    )
    type = OperationObjectTypeWhereFilter(
        AttributeTypeEnumFilterInput, method=filter_attribute_type
    )
    unit = OperationObjectTypeWhereFilter(
        MeasurementUnitsEnumFilterInput, method=filter_attribute_unit
    )
    in_collection = GlobalIDWhereFilter(method="filter_in_collection")
    in_category = GlobalIDWhereFilter(method="filter_in_category")
    value_required = BooleanWhereFilter()
    visible_in_storefront = BooleanWhereFilter()
    filterable_in_dashboard = BooleanWhereFilter()

    class Meta:
        model = Attribute
        fields = []

    def filter_in_collection(self, qs, name, value):
        requestor = get_user_or_app_from_context(self.request)
        channel_slug = get_channel_slug_from_filter_data(self.data)
        return where_filter_attributes_by_product_types(
            qs, name, value, requestor, channel_slug
        )

    def filter_in_category(self, qs, name, value):
        requestor = get_user_or_app_from_context(self.request)
        channel_slug = get_channel_slug_from_filter_data(self.data)
        return where_filter_attributes_by_product_types(
            qs, name, value, requestor, channel_slug
        )


class AttributeWhereInput(WhereInputObjectType):
    class Meta:
        filterset_class = AttributeWhere
        description = "Where filtering options." + ADDED_IN_311 + PREVIEW_FEATURE
        doc_category = DOC_CATEGORY_ATTRIBUTES
