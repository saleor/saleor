from typing import Literal, TypedDict

import django_filters
import graphene
from django.db.models import Exists, OuterRef, Q, QuerySet

from ...attribute import AttributeInputType
from ...attribute.models import AssignedPageAttributeValue, Attribute, AttributeValue
from ...channel.models import Channel
from ...page import models as page_models
from ...permission.utils import has_one_of_permissions
from ...product import models as product_models
from ...product.models import ALL_PRODUCTS_PERMISSIONS
from ..channel.filters import get_channel_slug_from_filter_data
from ..core.doc_category import DOC_CATEGORY_ATTRIBUTES
from ..core.enums import MeasurementUnitsEnum
from ..core.filters import (
    BooleanWhereFilter,
    ChannelFilterInputObjectType,
    EnumFilter,
    FilterInputObjectType,
    GlobalIDFilter,
    GlobalIDMultipleChoiceFilter,
    GlobalIDMultipleChoiceWhereFilter,
    GlobalIDWhereFilter,
    ListObjectTypeFilter,
    MetadataFilterBase,
    MetadataWhereFilterBase,
    OperationObjectTypeWhereFilter,
    WhereFilterSet,
)
from ..core.filters.where_input import (
    FilterInputDescriptions,
    StringFilterInput,
    WhereInputObjectType,
)
from ..core.types.base import BaseInputObjectType
from ..core.types.common import NonNullList
from ..core.utils import from_global_id_or_error
from ..utils import get_user_or_app_from_context
from ..utils.filters import filter_by_ids, filter_slug_list, filter_where_by_value_field
from .enums import AttributeEntityTypeEnum, AttributeInputTypeEnum, AttributeTypeEnum


def filter_attributes_by_product_types(qs, field, value, requestor, channel_slug):
    if not value:
        return qs

    channel = None
    if channel_slug is not None:
        channel = Channel.objects.using(qs.db).filter(slug=str(channel_slug)).first()
    limited_channel_access = False if channel_slug is None else True
    product_qs = product_models.Product.objects.using(qs.db).visible_to_user(
        requestor, channel, limited_channel_access
    )

    if field == "in_category":
        _type, category_id = from_global_id_or_error(value, "Category")
        category = (
            product_models.Category.objects.using(qs.db).filter(pk=category_id).first()
        )

        if category is None:
            return qs.none()

        tree = category.get_descendants(include_self=True)
        product_qs = product_qs.filter(category__in=tree)

        if not has_one_of_permissions(requestor, ALL_PRODUCTS_PERMISSIONS):
            product_qs = product_qs.annotate_visible_in_listings(channel).exclude(
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


def search_attribute_values(qs, value):
    name_slug_qs = Q(name__ilike=value) | Q(slug__ilike=value)
    return qs.filter(name_slug_qs)


class AttributeValueFilter(django_filters.FilterSet):
    search = django_filters.CharFilter(method="filter_search")
    ids = GlobalIDMultipleChoiceFilter(field_name="id")
    slugs = ListObjectTypeFilter(input_class=graphene.String, method=filter_slug_list)

    class Meta:
        model = AttributeValue
        fields = ["search"]

    @classmethod
    def filter_search(cls, queryset, _name, value):
        """Filter attribute values by name or slug."""
        if not value:
            return queryset
        return search_attribute_values(queryset, value)


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
    return filter_where_by_value_field(qs, "name", value)


def filter_attribute_slug(qs, _, value):
    return filter_where_by_value_field(qs, "slug", value)


def filter_with_choices(qs, _, value):
    lookup = Q(input_type__in=AttributeInputType.TYPES_WITH_CHOICES)
    if value is True:
        return qs.filter(lookup)
    if value is False:
        return qs.exclude(lookup)
    return qs.none()


def filter_attribute_input_type(qs, _, value):
    return filter_where_by_value_field(qs, "input_type", value)


def filter_attribute_entity_type(qs, _, value):
    return filter_where_by_value_field(qs, "entity_type", value)


def filter_attribute_type(qs, _, value):
    return filter_where_by_value_field(qs, "type", value)


def filter_attribute_unit(qs, _, value):
    return filter_where_by_value_field(qs, "unit", value)


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
        description = "Where filtering options."
        doc_category = DOC_CATEGORY_ATTRIBUTES


class AttributeValueWhere(WhereFilterSet):
    ids = GlobalIDMultipleChoiceWhereFilter(method=filter_by_ids("AttributeValue"))
    name = OperationObjectTypeWhereFilter(
        input_class=StringFilterInput, method="filter_by_name"
    )
    slug = OperationObjectTypeWhereFilter(
        input_class=StringFilterInput, method="filter_by_slug"
    )

    class Meta:
        model = AttributeValue
        fields = []

    @staticmethod
    def filter_by_name(qs, name, value):
        return filter_where_by_value_field(qs, "name", value)

    @staticmethod
    def filter_by_slug(qs, name, value):
        return filter_where_by_value_field(qs, "slug", value)


class AttributeValueWhereInput(WhereInputObjectType):
    class Meta:
        filterset_class = AttributeValueWhere
        description = "Where filtering options for attribute values."
        doc_category = DOC_CATEGORY_ATTRIBUTES


CONTAINS_TYPING = dict[Literal["contains_any", "contains_all"], list[str]]


class SharedContainsFilterParams(TypedDict):
    attr_id: int | None
    db_connection_name: str
    assigned_attr_model: type[AssignedPageAttributeValue]
    assigned_id_field_name: Literal["page_id"]
    identifier_field_name: Literal["slug", "id", "sku"]


def filter_by_contains_referenced_object_ids(
    attr_id: int | None,
    attr_value: CONTAINS_TYPING,
    db_connection_name: str,
    assigned_attr_model: type[AssignedPageAttributeValue],
    assigned_id_field_name: Literal["page_id"],
):
    """Build a filter expression for objects referencing other entities by global IDs.

    Returns a Q expression to filter objects based on their references
    to other entities (like: variants, products, pages), identified by
    global IDs.

    - If `contains_all` is provided, only objects that reference all of the
    specified global IDs will match.
    - If `contains_any` is provided, objects that reference at least one of
    the specified global IDs will match.
    """

    contains_all = attr_value.get("contains_all")
    contains_any = attr_value.get("contains_any")

    variant_ids = set()
    product_ids = set()
    page_ids = set()

    for obj_id in contains_any or contains_all or []:
        type_, id_ = graphene.Node.from_global_id(obj_id)
        if type_ == "Page":
            page_ids.add(id_)
        elif type_ == "Product":
            product_ids.add(id_)
        elif type_ == "ProductVariant":
            variant_ids.add(id_)

    expression = Q()
    shared_filter_params: SharedContainsFilterParams = {
        "attr_id": attr_id,
        "db_connection_name": db_connection_name,
        "assigned_attr_model": assigned_attr_model,
        "assigned_id_field_name": assigned_id_field_name,
        "identifier_field_name": "id",
    }
    if contains_all:
        if page_ids:
            expression &= _filter_contains_all_condition(
                contains_all=list(page_ids),
                referenced_model=page_models.Page,
                attr_value_reference_field_name="reference_page_id",
                **shared_filter_params,
            )
        if product_ids:
            expression &= _filter_contains_all_condition(
                contains_all=list(product_ids),
                referenced_model=product_models.Product,
                attr_value_reference_field_name="reference_product_id",
                **shared_filter_params,
            )
        if variant_ids:
            expression &= _filter_contains_all_condition(
                contains_all=list(variant_ids),
                referenced_model=product_models.ProductVariant,
                attr_value_reference_field_name="reference_variant_id",
                **shared_filter_params,
            )
        return expression

    if contains_any:
        if page_ids:
            expression |= _filter_contains_any_condition(
                contains_any=list(page_ids),
                referenced_model=page_models.Page,
                attr_value_reference_field_name="reference_page_id",
                **shared_filter_params,
            )

        if product_ids:
            expression |= _filter_contains_any_condition(
                contains_any=list(product_ids),
                referenced_model=product_models.Product,
                attr_value_reference_field_name="reference_product_id",
                **shared_filter_params,
            )

        if variant_ids:
            expression |= _filter_contains_any_condition(
                contains_any=list(variant_ids),
                referenced_model=product_models.ProductVariant,
                attr_value_reference_field_name="reference_variant_id",
                **shared_filter_params,
            )
    return expression


def _filter_contains_single_expression(
    attr_id: int | None,
    db_connection_name: str,
    reference_objs: QuerySet[
        page_models.Page | product_models.Product | product_models.ProductVariant
    ],
    attr_value_reference_field_name: Literal[
        "reference_page_id", "reference_product_id", "reference_variant_id"
    ],
    assigned_attr_model: type[AssignedPageAttributeValue],
    assigned_id_field_name: Literal["page_id"],
):
    single_reference_qs = AttributeValue.objects.using(db_connection_name).filter(
        Exists(reference_objs.filter(id=OuterRef(attr_value_reference_field_name))),
    )
    if attr_id:
        attr_query = Attribute.objects.using(db_connection_name).filter(id=attr_id)
        single_reference_qs = single_reference_qs.filter(
            Exists(attr_query.filter(id=OuterRef("attribute_id"))),
        )
    assigned_attr_value = assigned_attr_model.objects.using(db_connection_name).filter(
        Exists(single_reference_qs.filter(id=OuterRef("value_id"))),
        **{str(assigned_id_field_name): OuterRef("id")},
    )
    return Q(Exists(assigned_attr_value))


def _filter_contains_all_condition(
    attr_id: int | None,
    db_connection_name: str,
    contains_all: list[str],
    assigned_attr_model: type[AssignedPageAttributeValue],
    assigned_id_field_name: Literal["page_id"],
    identifier_field_name: Literal["slug", "id", "sku"],
    referenced_model: type[
        page_models.Page | product_models.Product | product_models.ProductVariant
    ],
    attr_value_reference_field_name: Literal[
        "reference_page_id", "reference_product_id", "reference_variant_id"
    ],
):
    """Build a filter expression that ensures all specified references are present.

    Constructs a Q expression that checks for references to all entities from
    `referenced_model`, matched using the provided identifiers in `contains_all`.

    For each identifier, it resolves the corresponding object using
    `identifier_field_name` and adds a subquery to verify the presence
    of that reference. The subqueries are combined using logical AND.
    """

    identifiers = contains_all
    expression = Q()

    for identifier in identifiers:
        reference_obj = referenced_model.objects.using(db_connection_name).filter(
            **{str(identifier_field_name): identifier}
        )
        expression &= _filter_contains_single_expression(
            attr_id,
            db_connection_name,
            reference_obj,
            attr_value_reference_field_name,
            assigned_attr_model,
            assigned_id_field_name,
        )
    return expression


def _filter_contains_any_condition(
    attr_id: int | None,
    db_connection_name: str,
    contains_any: list[str],
    assigned_attr_model: type[AssignedPageAttributeValue],
    assigned_id_field_name: Literal["page_id"],
    identifier_field_name: Literal["slug", "id", "sku"],
    referenced_model: type[
        page_models.Page | product_models.Product | product_models.ProductVariant
    ],
    attr_value_reference_field_name: Literal[
        "reference_page_id", "reference_product_id", "reference_variant_id"
    ],
):
    """Build a filter expression that ensures at least one specified reference is present.

    Constructs a Q expression that checks for a reference to any entity from
    `referenced_model`, matched using the provided identifiers in `contains_any`.

    All matching references are resolved using `identifier_field_name`,
    and passed as a single queryset to be checked in a single subquery.

    """
    identifiers = contains_any
    reference_objs = referenced_model.objects.using(db_connection_name).filter(
        **{f"{identifier_field_name}__in": identifiers}
    )
    return _filter_contains_single_expression(
        attr_id,
        db_connection_name,
        reference_objs,
        attr_value_reference_field_name,
        assigned_attr_model,
        assigned_id_field_name,
    )


def filter_by_contains_referenced_pages(
    attr_id: int | None,
    attr_value: CONTAINS_TYPING,
    db_connection_name: str,
    assigned_attr_model: type[AssignedPageAttributeValue],
    assigned_id_field_name: Literal["page_id"],
):
    """Build a filter expression for referenced pages.

    Returns a Q expression to filter objects based on their references
    to pages.

    - If `contains_all` is provided, only objects that reference all of the
    specified pages will match.
    - If `contains_any` is provided, objects that reference at least one of
    the specified pages will match.
    """
    contains_all = attr_value.get("contains_all")
    contains_any = attr_value.get("contains_any")

    shared_filter_params: SharedContainsFilterParams = {
        "attr_id": attr_id,
        "db_connection_name": db_connection_name,
        "assigned_attr_model": assigned_attr_model,
        "assigned_id_field_name": assigned_id_field_name,
        "identifier_field_name": "slug",
    }
    if contains_all:
        return _filter_contains_all_condition(
            contains_all=contains_all,
            referenced_model=page_models.Page,
            attr_value_reference_field_name="reference_page_id",
            **shared_filter_params,
        )

    if contains_any:
        return _filter_contains_any_condition(
            contains_any=contains_any,
            referenced_model=page_models.Page,
            attr_value_reference_field_name="reference_page_id",
            **shared_filter_params,
        )
    return Q()


def filter_by_contains_referenced_products(
    attr_id: int | None,
    attr_value: CONTAINS_TYPING,
    db_connection_name: str,
    assigned_attr_model: type[AssignedPageAttributeValue],
    assigned_id_field_name: Literal["page_id"],
):
    """Build a filter expression for referenced products.

    Returns a Q expression to filter objects based on their references
    to products.

    - If `contains_all` is provided, only objects that reference all of the
    specified products will match.
    - If `contains_any` is provided, objects that reference at least one of
    the specified products will match.
    """
    contains_all = attr_value.get("contains_all")
    contains_any = attr_value.get("contains_any")

    shared_filter_params: SharedContainsFilterParams = {
        "attr_id": attr_id,
        "db_connection_name": db_connection_name,
        "assigned_attr_model": assigned_attr_model,
        "assigned_id_field_name": assigned_id_field_name,
        "identifier_field_name": "slug",
    }

    if contains_all:
        return _filter_contains_all_condition(
            contains_all=contains_all,
            referenced_model=product_models.Product,
            attr_value_reference_field_name="reference_product_id",
            **shared_filter_params,
        )

    if contains_any:
        return _filter_contains_any_condition(
            contains_any=contains_any,
            referenced_model=product_models.Product,
            attr_value_reference_field_name="reference_product_id",
            **shared_filter_params,
        )
    return Q()


def filter_by_contains_referenced_variants(
    attr_id: int | None,
    attr_value: CONTAINS_TYPING,
    db_connection_name: str,
    assigned_attr_model: type[AssignedPageAttributeValue],
    assigned_id_field_name: Literal["page_id"],
):
    """Build a filter expression for referenced product variants.

    Returns a Q expression to filter objects based on their references
    to product variants.

    - If `contains_all` is provided, only objects that reference all of the
    specified variants will match.
    - If `contains_any` is provided, objects that reference at least one of
    the specified variants will match.
    """

    contains_all = attr_value.get("contains_all")
    contains_any = attr_value.get("contains_any")

    shared_filter_params: SharedContainsFilterParams = {
        "attr_id": attr_id,
        "db_connection_name": db_connection_name,
        "assigned_attr_model": assigned_attr_model,
        "assigned_id_field_name": assigned_id_field_name,
        "identifier_field_name": "sku",
    }

    if contains_all:
        return _filter_contains_all_condition(
            contains_all=contains_all,
            referenced_model=product_models.ProductVariant,
            attr_value_reference_field_name="reference_variant_id",
            **shared_filter_params,
        )

    if contains_any:
        return _filter_contains_any_condition(
            contains_any=contains_any,
            referenced_model=product_models.ProductVariant,
            attr_value_reference_field_name="reference_variant_id",
            **shared_filter_params,
        )
    return Q()
