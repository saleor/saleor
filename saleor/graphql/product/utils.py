from collections import defaultdict
from typing import TYPE_CHECKING, Dict, List, Tuple

import graphene
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q
from django.db.utils import IntegrityError

from ...attribute import AttributeInputType
from ...warehouse.models import Stock

if TYPE_CHECKING:
    from django.db.models import QuerySet
    from ...attribute.models import Attribute
    from ...product.models import ProductVariant
    from .mutations.products import AttrValuesInput


def validate_attributes_input(
    input_data: List[Tuple["Attribute", "AttrValuesInput"]],
    attribute_qs: "QuerySet",
    error_code_enum,
    *,
    variant_validation: bool,
):
    """Validate attribute input.

    - ensure all required attributes are passed
    - ensure the values are correct for a products or a page
    """

    error_no_value_given = ValidationError(
        "Attribute expects a value but none were given",
        code=error_code_enum.REQUIRED.value,
    )
    error_dropdown_get_more_than_one_value = ValidationError(
        "Attribute must take only one value", code=error_code_enum.INVALID.value,
    )
    error_blank_value = ValidationError(
        "Attribute values cannot be blank", code=error_code_enum.REQUIRED.value,
    )

    error_no_file_given = ValidationError(
        "Attribute file url cannot be blank", code=error_code_enum.REQUIRED.value,
    )
    error_blank_file_value = ValidationError(
        "Attribute expects a file url but none were given",
        code=error_code_enum.REQUIRED.value,
    )

    attribute_errors: Dict[ValidationError, List[str]] = defaultdict(list)
    for attribute, attr_values in input_data:
        attribute_id = graphene.Node.to_global_id("Attribute", attribute.pk)
        # validation for file attribute
        if attribute.input_type == AttributeInputType.FILE:
            value = attr_values.file_url
            if not value:
                if attribute.value_required or variant_validation:
                    attribute_errors[error_no_file_given].append(attribute_id)
                continue
            if value is None or not value.strip():
                attribute_errors[error_blank_file_value].append(attribute_id)
                continue
        # validation for other input types
        else:
            if not attr_values.values:
                if attribute.value_required or variant_validation:
                    attribute_errors[error_no_value_given].append(attribute_id)
                continue
            if (
                attribute.input_type != AttributeInputType.MULTISELECT
                and len(attr_values.values) != 1
            ):
                attribute_errors[error_dropdown_get_more_than_one_value].append(
                    attribute_id
                )
                continue
            for value in attr_values.values:
                if value is None or not value.strip():
                    attribute_errors[error_blank_value].append(attribute_id)
                    continue

    errors = prepare_error_list_from_error_attribute_mapping(attribute_errors)
    if not variant_validation:
        errors = validate_required_attributes(
            input_data, attribute_qs, errors, error_code_enum
        )

    return errors


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
            code=error_code_enum.REQUIRED.value,
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
        for variant in assigned_variant_attribute.values.all():
            attribute_values[attribute_id].append(variant.slug)
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
