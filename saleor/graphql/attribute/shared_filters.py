from typing import Literal, TypedDict

import graphene
from django.db.models import Exists, OuterRef, Q, QuerySet
from graphql import GraphQLError

from ...attribute import AttributeInputType
from ...attribute.models import (
    AssignedPageAttributeValue,
    AssignedProductAttributeValue,
    Attribute,
    AttributeValue,
)
from ...page import models as page_models
from ...product import models as product_models
from ..core.filters import DecimalFilterInput
from ..core.filters.where_input import ContainsFilterInput, StringFilterInput
from ..core.types import DateRangeInput, DateTimeRangeInput
from ..core.types.base import BaseInputObjectType
from ..utils.filters import (
    filter_range_field,
    filter_where_by_numeric_field,
    filter_where_by_value_field,
)


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
    assigned_attr_model: type[
        AssignedPageAttributeValue | AssignedProductAttributeValue
    ]
    assigned_id_field_name: Literal["page_id", "product_id"]
    identifier_field_name: Literal["slug", "id", "sku"]


def filter_by_contains_referenced_object_ids(
    attr_id: int | None,
    attr_value: CONTAINS_TYPING,
    db_connection_name: str,
    assigned_attr_model: type[
        AssignedPageAttributeValue | AssignedProductAttributeValue
    ],
    assigned_id_field_name: Literal["page_id", "product_id"],
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
    assigned_attr_model: type[
        AssignedPageAttributeValue | AssignedProductAttributeValue
    ],
    assigned_id_field_name: Literal["page_id", "product_id"],
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
    assigned_attr_model: type[
        AssignedPageAttributeValue | AssignedProductAttributeValue
    ],
    assigned_id_field_name: Literal["page_id", "product_id"],
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
    assigned_attr_model: type[
        AssignedPageAttributeValue | AssignedProductAttributeValue
    ],
    assigned_id_field_name: Literal["page_id", "product_id"],
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
    assigned_attr_model: type[
        AssignedPageAttributeValue | AssignedProductAttributeValue
    ],
    assigned_id_field_name: Literal["page_id", "product_id"],
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
    assigned_attr_model: type[
        AssignedPageAttributeValue | AssignedProductAttributeValue
    ],
    assigned_id_field_name: Literal["page_id", "product_id"],
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
    assigned_attr_model: type[
        AssignedPageAttributeValue | AssignedProductAttributeValue
    ],
    assigned_id_field_name: Literal["page_id", "product_id"],
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


def filter_by_slug_or_name(
    attr_id: int | None,
    attr_value: dict,
    db_connection_name: str,
    assigned_attr_model: type[
        AssignedPageAttributeValue | AssignedProductAttributeValue
    ],
    assigned_id_field_name: Literal["page_id", "product_id"],
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
    assigned_attr_value = assigned_attr_model.objects.using(db_connection_name).filter(
        Exists(attribute_values.filter(id=OuterRef("value_id"))),
        **{str(assigned_id_field_name): OuterRef("id")},
    )
    return Q(Exists(assigned_attr_value))


def filter_by_numeric_attribute(
    attr_id: int | None,
    numeric_value,
    db_connection_name: str,
    assigned_attr_model: type[
        AssignedPageAttributeValue | AssignedProductAttributeValue
    ],
    assigned_id_field_name: Literal["page_id", "product_id"],
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

    assigned_attr_value = assigned_attr_model.objects.using(db_connection_name).filter(
        value__in=qs_by_numeric,
        **{str(assigned_id_field_name): OuterRef("id")},
    )
    return Q(Exists(assigned_attr_value))


def filter_by_boolean_attribute(
    attr_id: int | None,
    boolean_value,
    db_connection_name: str,
    assigned_attr_model: type[
        AssignedPageAttributeValue | AssignedProductAttributeValue
    ],
    assigned_id_field_name: Literal["page_id", "product_id"],
):
    qs_by_boolean = AttributeValue.objects.using(db_connection_name).filter(
        attribute__input_type=AttributeInputType.BOOLEAN,
        **{"attribute_id": attr_id} if attr_id else {},
    )
    qs_by_boolean = qs_by_boolean.filter(boolean=boolean_value)
    assigned_attr_value = assigned_attr_model.objects.using(db_connection_name).filter(
        value__in=qs_by_boolean,
        **{str(assigned_id_field_name): OuterRef("id")},
    )
    return Q(Exists(assigned_attr_value))


def filter_by_date_attribute(
    attr_id: int | None,
    date_value,
    db_connection_name: str,
    assigned_attr_model: type[
        AssignedPageAttributeValue | AssignedProductAttributeValue
    ],
    assigned_id_field_name: Literal["page_id", "product_id"],
):
    qs_by_date = AttributeValue.objects.using(db_connection_name).filter(
        attribute__input_type=AttributeInputType.DATE,
        **{"attribute_id": attr_id} if attr_id else {},
    )
    qs_by_date = filter_range_field(
        qs_by_date,
        "date_time__date",
        date_value,
    )
    assigned_attr_value = assigned_attr_model.objects.using(db_connection_name).filter(
        value__in=qs_by_date,
        **{str(assigned_id_field_name): OuterRef("id")},
    )
    return Q(Exists(assigned_attr_value))


def filter_by_date_time_attribute(
    attr_id: int | None,
    date_time_value,
    db_connection_name: str,
    assigned_attr_model: type[
        AssignedPageAttributeValue | AssignedProductAttributeValue
    ],
    assigned_id_field_name: Literal["page_id", "product_id"],
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
    assigned_attr_value = assigned_attr_model.objects.using(db_connection_name).filter(
        value__in=qs_by_date_time,
        **{str(assigned_id_field_name): OuterRef("id")},
    )
    return Exists(assigned_attr_value)


def filter_objects_by_attributes[T: (page_models.Page, product_models.Product)](
    qs: QuerySet[T],
    value: list[dict],
    assigned_attr_model: type[
        AssignedPageAttributeValue | AssignedProductAttributeValue
    ],
    assigned_id_field_name: Literal["page_id", "product_id"],
) -> QuerySet[T]:
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
        assigned_attr_value = assigned_attr_model.objects.using(qs.db).filter(
            Exists(atr_value_qs.filter(id=OuterRef("value_id"))),
            **{str(assigned_id_field_name): OuterRef("id")},
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
                assigned_attr_model=assigned_attr_model,
                assigned_id_field_name=assigned_id_field_name,
            )
        elif "numeric" in attr_value:
            attr_filter_expression &= filter_by_numeric_attribute(
                attr_id,
                attr_value["numeric"],
                qs.db,
                assigned_attr_model=assigned_attr_model,
                assigned_id_field_name=assigned_id_field_name,
            )
        elif "boolean" in attr_value:
            attr_filter_expression &= filter_by_boolean_attribute(
                attr_id,
                attr_value["boolean"],
                qs.db,
                assigned_attr_model=assigned_attr_model,
                assigned_id_field_name=assigned_id_field_name,
            )
        elif "date" in attr_value:
            attr_filter_expression &= filter_by_date_attribute(
                attr_id,
                attr_value["date"],
                qs.db,
                assigned_attr_model=assigned_attr_model,
                assigned_id_field_name=assigned_id_field_name,
            )
        elif "date_time" in attr_value:
            attr_filter_expression &= filter_by_date_time_attribute(
                attr_id,
                attr_value["date_time"],
                qs.db,
                assigned_attr_model=assigned_attr_model,
                assigned_id_field_name=assigned_id_field_name,
            )
        elif "reference" in attr_value:
            attr_filter_expression &= filter_objects_by_reference_attributes(
                attr_id,
                attr_value["reference"],
                qs.db,
                assigned_attr_model=assigned_attr_model,
                assigned_id_field_name=assigned_id_field_name,
            )
    if attr_filter_expression != Q():
        return qs.filter(attr_filter_expression)
    return qs.none()


def filter_objects_by_reference_attributes(
    attr_id: int | None,
    attr_value: dict[
        Literal[
            "referenced_ids", "page_slugs", "product_slugs", "product_variant_skus"
        ],
        CONTAINS_TYPING,
    ],
    db_connection_name: str,
    assigned_attr_model: type[
        AssignedPageAttributeValue | AssignedProductAttributeValue
    ],
    assigned_id_field_name: Literal["page_id", "product_id"],
):
    filter_expression = Q()

    if "referenced_ids" in attr_value:
        filter_expression &= filter_by_contains_referenced_object_ids(
            attr_id,
            attr_value["referenced_ids"],
            db_connection_name,
            assigned_attr_model=assigned_attr_model,
            assigned_id_field_name=assigned_id_field_name,
        )
    if "page_slugs" in attr_value:
        filter_expression &= filter_by_contains_referenced_pages(
            attr_id,
            attr_value["page_slugs"],
            db_connection_name,
            assigned_attr_model=assigned_attr_model,
            assigned_id_field_name=assigned_id_field_name,
        )
    if "product_slugs" in attr_value:
        filter_expression &= filter_by_contains_referenced_products(
            attr_id,
            attr_value["product_slugs"],
            db_connection_name,
            assigned_attr_model=assigned_attr_model,
            assigned_id_field_name=assigned_id_field_name,
        )
    if "product_variant_skus" in attr_value:
        filter_expression &= filter_by_contains_referenced_variants(
            attr_id,
            attr_value["product_variant_skus"],
            db_connection_name,
            assigned_attr_model=assigned_attr_model,
            assigned_id_field_name=assigned_id_field_name,
        )
    return filter_expression


def validate_attribute_value_reference_input(
    index_with_values: list[
        tuple[
            str,
            dict[
                Literal[
                    "referenced_ids",
                    "page_slugs",
                    "product_slugs",
                    "product_variant_skus",
                ],
                CONTAINS_TYPING,
            ]
            | None,
        ]
    ],
):
    """Validate the input for reference attributes.

    This function checks if the input for reference attributes is valid.
    It raises a GraphQLError if the input is invalid.
    """

    duplicated_error = set()
    empty_input_value_error = set()
    invalid_input_type_error = set()
    for index, value in index_with_values:
        if not value:
            invalid_input_type_error.add(index)
            continue
        for key in value:
            single_key_value = value[key]
            if (
                "contains_all" in single_key_value
                and "contains_any" in single_key_value
            ):
                duplicated_error.add(index)
                continue
            if (
                "contains_all" in single_key_value
                and not single_key_value["contains_all"]
            ):
                empty_input_value_error.add(index)
                continue
            if (
                "contains_any" in single_key_value
                and not single_key_value["contains_any"]
            ):
                empty_input_value_error.add(index)

    if invalid_input_type_error:
        raise GraphQLError(
            message=(
                "Invalid input for reference attributes. For attribute input on positions: "
                f"{', '.join(invalid_input_type_error)}. "
                "Provided values must contains 'containsAll' or 'containsAny' key."
            )
        )
    if empty_input_value_error:
        raise GraphQLError(
            message=(
                "Invalid input for reference attributes. For attribute input on positions: "
                f"{', '.join(empty_input_value_error)}. "
                "Provided values cannot be null or empty."
            )
        )
    if duplicated_error:
        raise GraphQLError(
            message=(
                "Invalid input for reference attributes. For attribute input on positions: "
                f"{', '.join(duplicated_error)}. "
                "Cannot provide both 'containsAll' and 'containsAny' for the same reference filter."
            )
        )


def validate_attribute_value_input(attributes: list[dict], db_connection_name: str):
    slug_list = [attr.get("slug") for attr in attributes if "slug" in attr]
    value_as_empty_or_null_list = []
    value_more_than_one_list = []
    invalid_input_type_list = []
    reference_value_list = []
    if len(slug_list) != len(set(slug_list)):
        raise GraphQLError(
            message="Duplicated attribute slugs in attribute 'where' input are not allowed."
        )

    type_specific_value_with_attr_slug_list = {}
    for index, attr in enumerate(attributes):
        if not attr.get("value") and not attr.get("slug"):
            value_as_empty_or_null_list.append(str(index))
            continue

        attr_slug = attr.get("slug")
        attr_slug_provided_as_none = attr_slug is None and "slug" in attr
        if attr_slug_provided_as_none:
            value_as_empty_or_null_list.append(str(index))
            continue

        value_as_empty = "value" in attr and not attr["value"]
        if value_as_empty:
            value_as_empty_or_null_list.append(str(index))
            continue

        value = attr.get("value")
        if not value:
            continue

        value_keys = value.keys()
        if len(value_keys) > 1:
            value_more_than_one_list.append(str(index))
            continue
        value_key = list(value_keys)[0]
        if value_key not in ["slug", "name"] and attr_slug:
            type_specific_value_with_attr_slug_list[attr_slug] = (str(index), value_key)
        if value[value_key] is None:
            value_as_empty_or_null_list.append(str(index))
            continue
        if value_key == "reference":
            reference_value_list.append((str(index), value["reference"]))

    if type_specific_value_with_attr_slug_list:
        attribute_input_type_map = Attribute.objects.using(db_connection_name).in_bulk(
            type_specific_value_with_attr_slug_list.keys(),
            field_name="slug",
        )
        for attr_slug, (
            index_str,
            value_key,
        ) in type_specific_value_with_attr_slug_list.items():
            if attr_slug not in attribute_input_type_map:
                continue

            input_type = attribute_input_type_map[attr_slug].input_type
            if "numeric" == value_key and input_type != AttributeInputType.NUMERIC:
                invalid_input_type_list.append(index_str)
            if "date" == value_key and input_type != AttributeInputType.DATE:
                invalid_input_type_list.append(index_str)
            if "date_time" == value_key and input_type != AttributeInputType.DATE_TIME:
                invalid_input_type_list.append(index_str)
            if "boolean" == value_key and input_type != AttributeInputType.BOOLEAN:
                invalid_input_type_list.append(index_str)
            if "reference" == value_key and input_type != AttributeInputType.REFERENCE:
                invalid_input_type_list.append(index_str)

    validate_attribute_value_reference_input(reference_value_list)

    if value_as_empty_or_null_list:
        raise GraphQLError(
            message=(
                f"Incorrect input for attributes on position: {','.join(value_as_empty_or_null_list)}. "
                "Provided 'value' cannot be empty or null."
            )
        )
    if value_more_than_one_list:
        raise GraphQLError(
            message=(
                f"Incorrect input for attributes on position: {','.join(value_more_than_one_list)}. "
                "Provided 'value' must have only one input key."
            )
        )
    if invalid_input_type_list:
        raise GraphQLError(
            message=(
                f"Incorrect input for attributes on position: {','.join(invalid_input_type_list)}. "
                "Provided 'value' do not match the attribute input type."
            )
        )
