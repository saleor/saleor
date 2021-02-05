from collections import defaultdict
from typing import TYPE_CHECKING, Dict, List, Tuple

import graphene
from django.core.exceptions import ValidationError
from django.db.models import Q

from ....attribute import AttributeInputType
from ....attribute import models as attribute_models
from ....page.error_codes import PageErrorCode
from ....product.error_codes import ProductErrorCode
from . import AttrValuesInput

if TYPE_CHECKING:
    from django.db.models import QuerySet

    from ....attribute.models import Attribute


T_ERROR_DICT = Dict[Tuple[str, str], List[str]]


class AttributeInputErrors:
    """Define error message and error code for given error.

    All used error codes must be specified in PageErrorCode and ProductErrorCode.
    """

    ERROR_NO_VALUE_GIVEN = ("Attribute expects a value but none were given", "REQUIRED")
    ERROR_DROPDOWN_GET_MORE_THAN_ONE_VALUE = (
        "Attribute must take only one value",
        "INVALID",
    )
    ERROR_BLANK_VALUE = (
        "Attribute values cannot be blank",
        "REQUIRED",
    )

    # file errors
    ERROR_NO_FILE_GIVEN = (
        "Attribute file url cannot be blank",
        "REQUIRED",
    )
    ERROR_BLANK_FILE_VALUE = (
        "Attribute expects a file url but none were given",
        "REQUIRED",
    )

    # reference errors
    ERROR_NO_REFERENCE_GIVEN = (
        "Attribute expects an reference but none were given.",
        "REQUIRED",
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

    error_code_enum = PageErrorCode if is_page_attributes else ProductErrorCode
    attribute_errors: T_ERROR_DICT = defaultdict(list)
    for attribute, attr_values in input_data:
        attrs = (
            attribute,
            attr_values,
            attribute_errors,
            variant_validation,
        )
        if attribute.input_type == AttributeInputType.FILE:
            validate_file_attributes_input(*attrs)
        elif attribute.input_type == AttributeInputType.REFERENCE:
            validate_reference_attributes_input(*attrs)
        # validation for other input types
        else:
            validate_standard_attributes_input(*attrs)

    errors = prepare_error_list_from_error_attribute_mapping(
        attribute_errors, error_code_enum
    )
    if not variant_validation:
        errors = validate_required_attributes(
            input_data, attribute_qs, errors, error_code_enum
        )

    return errors


def validate_file_attributes_input(
    attribute: "Attribute",
    attr_values: "AttrValuesInput",
    attribute_errors: T_ERROR_DICT,
    variant_validation: bool,
):
    attribute_id = attr_values.global_id
    value = attr_values.file_url
    if not value:
        if attribute.value_required or (
            variant_validation and is_variant_selection_attribute(attribute)
        ):
            attribute_errors[AttributeInputErrors.ERROR_NO_FILE_GIVEN].append(
                attribute_id
            )
    elif not value.strip():
        attribute_errors[AttributeInputErrors.ERROR_BLANK_FILE_VALUE].append(
            attribute_id
        )


def validate_reference_attributes_input(
    attribute: "Attribute",
    attr_values: "AttrValuesInput",
    attribute_errors: T_ERROR_DICT,
    variant_validation: bool,
):
    attribute_id = attr_values.global_id
    references = attr_values.references
    if not references:
        if attribute.value_required or variant_validation:
            attribute_errors[AttributeInputErrors.ERROR_NO_REFERENCE_GIVEN].append(
                attribute_id
            )


def validate_standard_attributes_input(
    attribute: "Attribute",
    attr_values: "AttrValuesInput",
    attribute_errors: T_ERROR_DICT,
    variant_validation: bool,
):
    attribute_id = attr_values.global_id
    if not attr_values.values:
        if attribute.value_required or (
            variant_validation and is_variant_selection_attribute(attribute)
        ):
            attribute_errors[AttributeInputErrors.ERROR_NO_VALUE_GIVEN].append(
                attribute_id
            )
    elif (
        attribute.input_type != AttributeInputType.MULTISELECT
        and len(attr_values.values) != 1
    ):
        attribute_errors[
            AttributeInputErrors.ERROR_DROPDOWN_GET_MORE_THAN_ONE_VALUE
        ].append(attribute_id)
    for value in attr_values.values:
        if value is None or not value.strip():
            attribute_errors[AttributeInputErrors.ERROR_BLANK_VALUE].append(
                attribute_id
            )


def is_variant_selection_attribute(attribute: attribute_models.Attribute):
    return attribute.input_type in AttributeInputType.ALLOWED_IN_VARIANT_SELECTION


def validate_required_attributes(
    input_data: List[Tuple["Attribute", "AttrValuesInput"]],
    attribute_qs: "QuerySet",
    errors: List[ValidationError],
    error_code_enum,
):
    """Ensure all required attributes are supplied."""

    supplied_attribute_pk = [attribute.pk for attribute, _ in input_data]

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
    attribute_errors: T_ERROR_DICT, error_code_enum
):
    errors = []
    for error_data, attributes in attribute_errors.items():
        error_msg, error_type = error_data
        error = ValidationError(
            error_msg,
            code=getattr(error_code_enum, error_type).value,
            params={"attributes": attributes},
        )
        errors.append(error)

    return errors
