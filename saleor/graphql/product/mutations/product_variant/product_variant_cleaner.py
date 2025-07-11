from collections import defaultdict

from django.core.exceptions import ValidationError

from .....attribute import models as attribute_models
from .....product.error_codes import ProductErrorCode
from ....attribute.utils.shared import (
    AttrValuesInput,
    get_values_from_attribute_values_input,
)

T_INPUT_MAP = list[tuple[attribute_models.Attribute, AttrValuesInput]]


def clean_weight(cleaned_input: dict):
    weight = cleaned_input.get("weight")
    if weight and weight.value < 0:
        raise ValidationError(
            {
                "weight": ValidationError(
                    "Product variant can't have negative weight.",
                    code=ProductErrorCode.INVALID.value,
                )
            }
        )


def clean_quantity_limit(cleaned_input: dict):
    quantity_limit_per_customer = cleaned_input.get("quantity_limit_per_customer")
    if quantity_limit_per_customer is not None and quantity_limit_per_customer < 1:
        raise ValidationError(
            {
                "quantity_limit_per_customer": ValidationError(
                    (
                        "Product variant can't have "
                        "quantity_limit_per_customer lower than 1."
                    ),
                    code=ProductErrorCode.INVALID.value,
                )
            }
        )


def clean_preorder_settings(cleaned_input: dict):
    preorder_settings = cleaned_input.get("preorder")
    if preorder_settings:
        cleaned_input["is_preorder"] = True
        cleaned_input["preorder_global_threshold"] = preorder_settings.get(
            "global_threshold"
        )
        cleaned_input["preorder_end_date"] = preorder_settings.get("end_date")


def validate_duplicated_attribute_values(
    attributes_data: T_INPUT_MAP,
    used_attribute_values: list[dict[str, list[str]]],
):
    attribute_values: defaultdict[str, list[str]] = defaultdict(list)
    for attr, attr_data in attributes_data:
        values = get_values_from_attribute_values_input(attr, attr_data)
        if attr_data.global_id:
            attribute_values[attr_data.global_id].extend(values)

    if attribute_values in used_attribute_values:
        raise ValidationError(
            "Duplicated attribute values for product variant.",
            code=ProductErrorCode.DUPLICATED_INPUT_ITEM.value,
            params={"attributes": attribute_values.keys()},
        )
    used_attribute_values.append(attribute_values)
