from typing import Literal, TypedDict

import graphene
from django.db.models import Exists, OuterRef, Q, QuerySet

from ...attribute.models import AssignedPageAttributeValue, Attribute, AttributeValue
from ...page import models as page_models
from ...product import models as product_models
from ..core.filters import (
    DecimalFilterInput,
)
from ..core.filters.where_input import (
    ContainsFilterInput,
    StringFilterInput,
)
from ..core.types import DateRangeInput, DateTimeRangeInput
from ..core.types.base import BaseInputObjectType


class AssignedAttributeReferenceInput(BaseInputObjectType):
    referenced_ids = ContainsFilterInput(
        description="Returns objects with a reference pointing to an object identified by the given ID.",
    )
    page_slugs = ContainsFilterInput(
        description="Returns objects with a reference pointing to a page identified by the given slug.",
    )
    product_slugs = ContainsFilterInput(
        description=(
            "Returns objects with a reference pointing to a product identified by the given slug."
        )
    )
    product_variant_skus = ContainsFilterInput(
        description=(
            "Returns objects with a reference pointing "
            "to a product variant identified by the given sku."
        )
    )


class AssignedAttributeValueInput(BaseInputObjectType):
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
    reference = AssignedAttributeReferenceInput(
        required=False,
        description="Filter by reference attribute value.",
    )


class AssignedAttributeWhereInput(BaseInputObjectType):
    slug = graphene.String(description="Filter by attribute slug.", required=False)
    value = AssignedAttributeValueInput(
        required=False,
        description=(
            "Filter by value of the attribute. Only one value input field is allowed. "
            "If provided more than one, the error will be raised."
        ),
    )


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
