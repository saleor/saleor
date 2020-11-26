from collections import defaultdict
from typing import TYPE_CHECKING, Dict, List, Tuple

import graphene
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q
from django.db.utils import IntegrityError

from ...attribute import AttributeInputType
from ...page.error_codes import PageErrorCode
from ...product.error_codes import ProductErrorCode
from ...warehouse.models import Stock

if TYPE_CHECKING:
    from django.db.models import QuerySet
    from ...attribute.models import Attribute
    from ...product.models import ProductVariant
    from .mutations.products import AttrValuesInput


class ProductAttributeInputErrors:
    ERROR_NO_VALUE_GIVEN = ValidationError(
        "Attribute expects a value but none were given",
        code=PageErrorCode.REQUIRED.value,
    )
    ERROR_DROPDOWN_GET_MORE_THAN_ONE_VALUE = ValidationError(
        "Attribute must take only one value", code=PageErrorCode.INVALID.value,
    )
    ERROR_BLANK_VALUE = ValidationError(
        "Attribute values cannot be blank", code=PageErrorCode.REQUIRED.value,
    )

    # file errors
    ERROR_NO_FILE_GIVEN = ValidationError(
        "Attribute file url cannot be blank", code=PageErrorCode.REQUIRED.value,
    )
    ERROR_BLANK_FILE_VALUE = ValidationError(
        "Attribute expects a file url but none were given",
        code=PageErrorCode.REQUIRED.value,
    )


class PageAttributeInputErrors:
    ERROR_NO_VALUE_GIVEN = ValidationError(
        "Attribute expects a value but none were given",
        code=ProductErrorCode.REQUIRED.value,
    )
    ERROR_DROPDOWN_GET_MORE_THAN_ONE_VALUE = ValidationError(
        "Attribute must take only one value", code=ProductErrorCode.INVALID.value,
    )
    ERROR_BLANK_VALUE = ValidationError(
        "Attribute values cannot be blank", code=ProductErrorCode.REQUIRED.value,
    )

    # file errors
    ERROR_NO_FILE_GIVEN = ValidationError(
        "Attribute file url cannot be blank", code=ProductErrorCode.REQUIRED.value,
    )
    ERROR_BLANK_FILE_VALUE = ValidationError(
        "Attribute expects a file url but none were given",
        code=ProductErrorCode.REQUIRED.value,
    )


def validate_attributes_input(
    input_data: List[Tuple["Attribute", "AttrValuesInput"]],
    attribute_qs: "QuerySet",
    *,
    is_page_attributes: bool,
    variant_validation: bool,
):
    """Validate attribute input.

    - ensure all required attributes are passed
    - ensure the values are correct for a products or a page
    """

    errors_data_structure = (
        PageAttributeInputErrors if is_page_attributes else ProductAttributeInputErrors
    )
    attribute_errors: Dict[ValidationError, List[str]] = defaultdict(list)
    for attribute, attr_values in input_data:
        # validation for file attribute
        if attribute.input_type == AttributeInputType.FILE:
            validate_file_attributes_input(
                attribute,
                attr_values,
                errors_data_structure,
                attribute_errors,
                variant_validation,
            )
        # validation for other input types
        else:
            validate_not_file_attributes_input(
                attribute,
                attr_values,
                errors_data_structure,
                attribute_errors,
                variant_validation,
            )

    errors = prepare_error_list_from_error_attribute_mapping(attribute_errors)
    if not variant_validation:
        errors = validate_required_attributes(
            input_data, attribute_qs, errors, is_page_attributes
        )

    return errors


def validate_file_attributes_input(
    attribute: "Attribute",
    attr_values: "AttrValuesInput",
    errors_data_structure,
    attribute_errors: Dict[ValidationError, List[str]],
    variant_validation: bool,
):
    attribute_id = attr_values.global_id
    value = attr_values.file_url
    if not value:
        if attribute.value_required or variant_validation:
            attribute_errors[errors_data_structure.ERROR_NO_FILE_GIVEN].append(
                attribute_id
            )
    elif not value.strip():
        attribute_errors[errors_data_structure.ERROR_BLANK_FILE_VALUE].append(
            attribute_id
        )


def validate_not_file_attributes_input(
    attribute: "Attribute",
    attr_values: "AttrValuesInput",
    errors_data_structure,
    attribute_errors: Dict[ValidationError, List[str]],
    variant_validation: bool,
):
    attribute_id = attr_values.global_id
    if not attr_values.values:
        if attribute.value_required or variant_validation:
            attribute_errors[errors_data_structure.ERROR_NO_VALUE_GIVEN].append(
                attribute_id
            )
    elif (
        attribute.input_type != AttributeInputType.MULTISELECT
        and len(attr_values.values) != 1
    ):
        attribute_errors[
            errors_data_structure.ERROR_DROPDOWN_GET_MORE_THAN_ONE_VALUE
        ].append(attribute_id)
    for value in attr_values.values:
        if value is None or not value.strip():
            attribute_errors[errors_data_structure.ERROR_BLANK_VALUE].append(
                attribute_id
            )


def validate_required_attributes(
    input_data: List[Tuple["Attribute", "AttrValuesInput"]],
    attribute_qs: "QuerySet",
    errors: List[ValidationError],
    is_page_attributes: bool,
):
    """Ensure all required attributes are supplied."""

    supplied_attribute_pk = [attribute.pk for attribute, _ in input_data]
    error_code_enum = PageErrorCode if is_page_attributes else ProductErrorCode

    missing_required_attributes = attribute_qs.filter(
        Q(value_required=True) & ~Q(pk__in=supplied_attribute_pk)
    )

    if missing_required_attributes:
        ids = [
            graphene.Node.to_global_id("Attribute", attr.pk)
            for attr in missing_required_attributes
        ]
        error = ValidationError(
            "All attributes flagged as having a value required must be supplied.",
            code=error_code_enum.REQUIRED.value,  # type: ignore
            params={"attributes": ids},
        )
        errors.append(error)

    return errors


def prepare_error_list_from_error_attribute_mapping(
    attribute_errors: Dict[ValidationError, List[str]]
):
    errors = []
    for error, attributes in attribute_errors.items():
        error.params = {"attributes": attributes}
        errors.append(error)

    return errors


def get_used_attribute_values_for_variant(variant):
    """Create a dict of attributes values for variant.

    Sample result is:
    {
        "attribute_1_global_id": ["ValueAttr1_1"],
        "attribute_2_global_id": ["ValueAttr2_1"]
    }
    """
    attribute_values = defaultdict(list)
    for assigned_variant_attribute in variant.attributes.all():
        attribute = assigned_variant_attribute.attribute
        attribute_id = graphene.Node.to_global_id("Attribute", attribute.id)
        for attr_value in assigned_variant_attribute.values.all():
            attribute_values[attribute_id].append(attr_value.slug)
    return attribute_values


def get_used_variants_attribute_values(product):
    """Create list of attributes values for all existing `ProductVariants` for product.

    Sample result is:
    [
        {
            "attribute_1_global_id": ["ValueAttr1_1"],
            "attribute_2_global_id": ["ValueAttr2_1"]
        },
        ...
        {
            "attribute_1_global_id": ["ValueAttr1_2"],
            "attribute_2_global_id": ["ValueAttr2_2"]
        }
    ]
    """
    variants = (
        product.variants.prefetch_related("attributes__values")
        .prefetch_related("attributes__assignment")
        .all()
    )
    used_attribute_values = []
    for variant in variants:
        attribute_values = get_used_attribute_values_for_variant(variant)
        used_attribute_values.append(attribute_values)
    return used_attribute_values


@transaction.atomic
def create_stocks(
    variant: "ProductVariant", stocks_data: List[Dict[str, str]], warehouses: "QuerySet"
):
    try:
        Stock.objects.bulk_create(
            [
                Stock(
                    product_variant=variant,
                    warehouse=warehouse,
                    quantity=stock_data["quantity"],
                )
                for stock_data, warehouse in zip(stocks_data, warehouses)
            ]
        )
    except IntegrityError:
        msg = "Stock for one of warehouses already exists for this product variant."
        raise ValidationError(msg)
