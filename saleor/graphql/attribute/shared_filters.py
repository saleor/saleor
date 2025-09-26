from typing import Literal, TypedDict, cast

import graphene
from django.db.models import Exists, OuterRef, QuerySet
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
from ..core.utils import from_global_id_or_error
from ..utils.filters import (
    Number,
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
    category_slugs = ContainsFilterInput(
        description=(
            "Returns objects with a reference pointing "
            "to a category identified by the given slug."
        )
    )
    collection_slugs = ContainsFilterInput(
        description=(
            "Returns objects with a reference pointing "
            "to a collection identified by the given slug."
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


def get_attribute_values_by_slug_or_name_value(
    attr_id: int | None,
    attr_value: dict,
    db_connection_name: str,
) -> QuerySet[AttributeValue]:
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
    return attribute_values


def get_attribute_values_by_numeric_value(
    attr_id: int | None,
    numeric_value: dict[str, Number | list[Number] | dict[str, Number]],
    db_connection_name: str,
) -> QuerySet[AttributeValue]:
    qs_by_numeric = AttributeValue.objects.using(db_connection_name).filter(
        attribute__input_type=AttributeInputType.NUMERIC,
        **{"attribute_id": attr_id} if attr_id else {},
    )
    qs_by_numeric = filter_where_by_numeric_field(
        qs_by_numeric,
        "numeric",
        numeric_value,
    )
    return qs_by_numeric


def get_attribute_values_by_boolean_value(
    attr_id: int | None,
    boolean_value: bool,
    db_connection_name: str,
) -> QuerySet[AttributeValue]:
    qs_by_boolean = AttributeValue.objects.using(db_connection_name).filter(
        attribute__input_type=AttributeInputType.BOOLEAN,
        **{"attribute_id": attr_id} if attr_id else {},
    )
    return qs_by_boolean.filter(boolean=boolean_value)


def get_attribute_values_by_date_value(
    attr_id: int | None,
    date_value: dict[str, str],
    db_connection_name: str,
) -> QuerySet[AttributeValue]:
    qs_by_date = AttributeValue.objects.using(db_connection_name).filter(
        attribute__input_type=AttributeInputType.DATE,
        **{"attribute_id": attr_id} if attr_id else {},
    )
    return filter_range_field(
        qs_by_date,
        "date_time__date",
        date_value,
    )


def get_attribute_values_by_date_time_value(
    attr_id: int | None,
    date_value: dict[str, str],
    db_connection_name: str,
) -> QuerySet[AttributeValue]:
    qs_by_date = AttributeValue.objects.using(db_connection_name).filter(
        attribute__input_type=AttributeInputType.DATE_TIME,
        **{"attribute_id": attr_id} if attr_id else {},
    )
    return filter_range_field(
        qs_by_date,
        "date_time",
        date_value,
    )


def _get_attribute_values_by_referenced_page_identifiers(
    field_name: str,
    identifiers: list[str] | list[int],
    db_connection_name: str,
):
    pages = page_models.Page.objects.using(db_connection_name).filter(
        **{f"{field_name}__in": identifiers}
    )
    return AttributeValue.objects.using(db_connection_name).filter(
        Exists(pages.filter(id=OuterRef("reference_page_id"))),
    )


def get_attribute_values_by_referenced_page_slugs(
    slugs: list[str], db_connection_name: str
) -> QuerySet[AttributeValue]:
    return _get_attribute_values_by_referenced_page_identifiers(
        "slug", slugs, db_connection_name
    )


def get_attribute_values_by_referenced_page_ids(
    ids: list[int], db_connection_name: str
) -> QuerySet[AttributeValue]:
    return _get_attribute_values_by_referenced_page_identifiers(
        "id", ids, db_connection_name
    )


def _get_attribute_values_by_referenced_product_identifiers(
    field_name: str,
    identifiers: list[str] | list[int],
    db_connection_name: str,
) -> QuerySet[AttributeValue]:
    products = product_models.Product.objects.using(db_connection_name).filter(
        **{f"{field_name}__in": identifiers}
    )
    return AttributeValue.objects.using(db_connection_name).filter(
        Exists(products.filter(id=OuterRef("reference_product_id"))),
    )


def get_attribute_values_by_referenced_category_slugs(
    slugs: list[str], db_connection_name: str
) -> QuerySet[AttributeValue]:
    return _get_attribute_values_by_referenced_category_identifiers(
        "slug", slugs, db_connection_name
    )


def get_attribute_values_by_referenced_category_ids(
    ids: list[int], db_connection_name: str
) -> QuerySet[AttributeValue]:
    return _get_attribute_values_by_referenced_category_identifiers(
        "id", ids, db_connection_name
    )


def _get_attribute_values_by_referenced_category_identifiers(
    field_name: str,
    identifiers: list[str] | list[int],
    db_connection_name: str,
) -> QuerySet[AttributeValue]:
    categories = product_models.Category.objects.using(db_connection_name).filter(
        **{f"{field_name}__in": identifiers}
    )
    return AttributeValue.objects.using(db_connection_name).filter(
        Exists(categories.filter(id=OuterRef("reference_category_id"))),
    )


def get_attribute_values_by_referenced_collection_slugs(
    slugs: list[str], db_connection_name: str
) -> QuerySet[AttributeValue]:
    return _get_attribute_values_by_referenced_collection_identifiers(
        "slug", slugs, db_connection_name
    )


def get_attribute_values_by_referenced_collection_ids(
    ids: list[int], db_connection_name: str
) -> QuerySet[AttributeValue]:
    return _get_attribute_values_by_referenced_collection_identifiers(
        "id", ids, db_connection_name
    )


def _get_attribute_values_by_referenced_collection_identifiers(
    field_name: str,
    identifiers: list[str] | list[int],
    db_connection_name: str,
) -> QuerySet[AttributeValue]:
    collections = product_models.Collection.objects.using(db_connection_name).filter(
        **{f"{field_name}__in": identifiers}
    )
    return AttributeValue.objects.using(db_connection_name).filter(
        Exists(collections.filter(id=OuterRef("reference_collection_id"))),
    )


def get_attribute_values_by_referenced_product_slugs(
    slugs: list[str], db_connection_name: str
) -> QuerySet[AttributeValue]:
    return _get_attribute_values_by_referenced_product_identifiers(
        "slug", slugs, db_connection_name
    )


def get_attribute_values_by_referenced_product_ids(
    ids: list[int], db_connection_name: str
) -> QuerySet[AttributeValue]:
    return _get_attribute_values_by_referenced_product_identifiers(
        "id", ids, db_connection_name
    )


def _get_attribute_values_by_referenced_variant_identifiers(
    field_name: str,
    identifiers: list[str] | list[int],
    db_connection_name: str,
):
    variants = product_models.ProductVariant.objects.using(db_connection_name).filter(
        **{f"{field_name}__in": identifiers}
    )
    return AttributeValue.objects.using(db_connection_name).filter(
        Exists(variants.filter(id=OuterRef("reference_variant_id"))),
    )


def get_attribute_values_by_referenced_variant_skus(
    slugs: list[str], db_connection_name: str
) -> QuerySet[AttributeValue]:
    return _get_attribute_values_by_referenced_variant_identifiers(
        "sku", slugs, db_connection_name
    )


def get_attribute_values_by_referenced_variant_ids(
    ids: list[int], db_connection_name: str
) -> QuerySet[AttributeValue]:
    return _get_attribute_values_by_referenced_variant_identifiers(
        "id", ids, db_connection_name
    )


def clean_up_referenced_global_ids(global_ids: list[str]) -> dict[str, set[int]]:
    grouped_ids: dict[str, set[int]] = {
        "Product": set(),
        "ProductVariant": set(),
        "Page": set(),
        "Category": set(),
        "Collection": set(),
    }
    for global_id in global_ids:
        type_, id_ = graphene.Node.from_global_id(global_id)
        if type_ in grouped_ids:
            id_ = cast(int, id_)
            grouped_ids[type_].add(id_)
    return grouped_ids


def _has_valid_reference_global_id(global_id: "str") -> bool:
    try:
        obj_type, _ = from_global_id_or_error(global_id)
    except GraphQLError:
        return False

    if obj_type not in (
        "Page",
        "Product",
        "ProductVariant",
        "Category",
        "Collection",
    ):
        return False
    return True


def _has_valid_reference_global_ids(
    single_key_value: CONTAINS_TYPING,
) -> bool:
    for global_id in single_key_value.get("contains_all", []):
        if not _has_valid_reference_global_id(global_id):
            return False
    for global_id in single_key_value.get("contains_any", []):
        if not _has_valid_reference_global_id(global_id):
            return False
    return True


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
                    "category_slugs",
                    "collection_slugs",
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
    invalid_reference_global_id_error = set()
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
            if key == "referenced_ids":
                if not _has_valid_reference_global_ids(single_key_value):
                    invalid_reference_global_id_error.add(index)

    if invalid_reference_global_id_error:
        raise GraphQLError(
            message=(
                "Invalid input for reference attributes. For attribute input on positions: "
                f"{', '.join(invalid_reference_global_id_error)}. "
                "Provided values must contain valid global IDs."
            )
        )
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
            if "reference" == value_key and input_type not in [
                AttributeInputType.REFERENCE,
                AttributeInputType.SINGLE_REFERENCE,
            ]:
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
