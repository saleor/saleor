from collections import defaultdict
from typing import TYPE_CHECKING, Dict, List, Optional, Tuple, Union

import graphene
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q
from django.db.utils import IntegrityError

from ...attribute import AttributeInputType
from ...product.error_codes import ProductErrorCode
from ...warehouse.models import Stock

if TYPE_CHECKING:
    from django.db.models import QuerySet
    from ...account import models as account_models
    from ...attribute.models import Attribute
    from ...product.models import ProductVariant
    from ..account import types as account_types


def validate_attributes_input_for_product_and_page(
    input_data: List[Tuple["Attribute", List[str]]],
    attribute_qs: "QuerySet",
    error_code_enum,
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
        "Attribute attribute must take only one value",
        code=error_code_enum.INVALID.value,
    )
    error_blank_value = ValidationError(
        "Attribute values cannot be blank", code=error_code_enum.REQUIRED.value,
    )

    attribute_errors: Dict[ValidationError, List[str]] = defaultdict(list)
    for attribute, values in input_data:
        attribute_id = graphene.Node.to_global_id("Attribute", attribute.pk)
        if not values:
            if attribute.value_required:
                attribute_errors[error_no_value_given].append(attribute_id)
            continue

        if attribute.input_type != AttributeInputType.MULTISELECT and len(values) != 1:
            attribute_errors[error_dropdown_get_more_than_one_value].append(
                attribute_id
            )
            continue

        for value in values:
            if value is None or not value.strip():
                attribute_errors[error_blank_value].append(attribute_id)
                continue

    errors = prepare_error_list_from_error_attribute_mapping(attribute_errors)
    errors = validate_required_attributes(
        input_data, attribute_qs, errors, error_code_enum
    )

    return errors


def validate_required_attributes(
    input_data: List[Tuple["Attribute", List[str]]],
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


def validate_attributes_input_for_variant(
    input_data: List[Tuple["Attribute", List[str]]]
):
    error_no_value_given = ValidationError(
        "Attribute expects a value but none were given",
        code=ProductErrorCode.REQUIRED.value,
    )
    error_more_than_one_value_given = ValidationError(
        "A variant attribute cannot take more than one value",
        code=ProductErrorCode.INVALID.value,
    )
    error_blank_value = ValidationError(
        "Attribute values cannot be blank", code=ProductErrorCode.REQUIRED.value,
    )

    attribute_errors: Dict[ValidationError, List[str]] = defaultdict(list)
    for attribute, values in input_data:
        attribute_id = graphene.Node.to_global_id("Attribute", attribute.pk)
        if not values:
            attribute_errors[error_no_value_given].append(attribute_id)
            continue

        if len(values) != 1:
            attribute_errors[error_more_than_one_value_given].append(attribute_id)
            continue

        if values[0] is None or not values[0].strip():
            attribute_errors[error_blank_value].append(attribute_id)

    return prepare_error_list_from_error_attribute_mapping(attribute_errors)


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


def get_country_for_stock_and_tax_calculation(
    destination_address: Optional[
        Union["account_types.AddressInput", "account_models.Address"]
    ] = None,
    company_address: Optional["account_models.Address"] = None,
) -> str:
    """Get country code needed for stock quantity validation and tax calculations.

    Country code for checkout is based on shipping address. If shipping address is not
    provided, try to use the company address configured in the shop settings. If this
    address is not set, fallback to the `DEFAULT_COUNTRY` setting.
    """
    if destination_address and destination_address.country:
        return destination_address.country
    elif company_address and company_address.country:
        return company_address.country.code
    else:
        return settings.DEFAULT_COUNTRY
